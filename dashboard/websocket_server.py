#!/usr/bin/env python

# WS server example

import asyncio
import websockets, datetime, random, time
from threading import Thread, Event
import json
from concurrent.futures import ThreadPoolExecutor
from settings import *
from binance.client import BinanceRESTAPI
from dashboard.logging_socket_handler import WebSocketFormatter, SocketHandler
import logging

logger = logging.getLogger('RenkoBot')

class KlinesServer(Thread):

    client = BinanceRESTAPI(API_KEY, API_SECRET)

    def __init__(self, loop, config):
        Thread.__init__(self)
        self.loop = loop
        self.klines = []
        #self.kline_event = asyncio.Event(loop=loop)
        self.kline_event = Event()
        self.config = config
        self.renko_bot = None
        self.websocket = None

    def get_klines(self):
        self.kline_event.wait()
        new_klines = []
        for kline in self.klines:
            kline_r = {
                          "close": kline.close,
                          "open": kline.open,
                          "high": kline.high,
                          "low": kline.low,
                          "close_time": kline.end_time,
                          "volume": kline.volume
                      }
            self.klines.pop(0)
            new_klines.append(kline_r)
        self.kline_event.clear()
        return new_klines

    async def send_klines(self):
        print("**************************************")
        print("sending klines is running")
        while True:
            klines = await self.loop.run_in_executor(None, self.get_klines)
            if klines:
                resp = {
                    "type": "klines",
                    "data": klines
                }
                if self.websocket:
                    await self.websocket.send(json.dumps(resp))

    async def send_info(self):

        if self.renko_bot:
            if self.renko_bot.up_trend and not self.renko_bot.down_trend:
                position = "BUY"
            elif self.renko_bot.down_trend and not self.renko_bot.up_trend:
                position = "SELL"
            else:
                position = "ERROR"
        else:
            position = ""

        info = {
            'type' : 'info',
            'pair' : self.config.symbol,
            'time_frame' : self.config.time_frame,
            'brick_size' : self.config.brick_size,
            'position' : position
        }
        await self.websocket.send(json.dumps(info))

    async def send_historical_klines(self):
        historical_klines = self.client.klines(symbol=self.config.symbol, interval=self.config.time_frame)
        if self.websocket:
            klines_array = []
            for kline in historical_klines:
                kline_r = {
                    "close": kline.close,
                    "open": kline.open,
                    "high": kline.high,
                    "low": kline.low,
                    "close_time": kline.close_time,
                    "volume": kline.volume
                }
                klines_array.append(kline_r)
            resp = {
                "type" : "klines",
                "data" : klines_array
            }
            await self.websocket.send(json.dumps(resp))

    def get_logs(self):
        self.log_event.wait()
        print("[+] New log!!")
        logs = []
        while self.log_list:
            log1 = {'time': int(time.time()) * 1000, 'log': self.log_list[0]}
            logs.append(log1)
            self.log_list.pop(0)
        self.log_event.clear()
        return logs

    async def send_logs(self):
        print("starting the send log server")
        self.log_list = []
        self.log_event = Event()
        wh = SocketHandler(self.log_list, self.log_event)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(wh)
        logs = [
            {'time': int(time.time()) * 1000, 'log': "starting log server"},
            {'time': int(time.time()) * 1000, 'log': "only major events are logged"},
            {'time': int(time.time()) * 1000, 'log': "only closed klines are logged, open klines not logged"}
        ]
        while True:
            print("[+] Recieved a new log, {}".format(logs))
            if logs:
                resp = {
                    "type": "logs",
                    "data": logs
                }
                if self.websocket:
                    await self.websocket.send(json.dumps(resp))
            logs = await self.loop.run_in_executor(None, self.get_logs)

    async def consumer(self):
        while True:
            if not self.websocket:
                print("websocket not ready")
                asyncio.sleep(5)
                continue
            data = await self.websocket.recv()
            action_data = json.loads(data)
            action = action_data['action']
            print(f"recieved a new action {action}")
            if "send_info" in action:
                print("sending info")
                await self.send_info()
            elif "send_historical_klines" in action:
                print("sending historical data")
                await self.send_historical_klines()
            elif "send_klines" in action:
                asyncio.ensure_future(self.send_klines())
            elif "send_logs" in action:
                asyncio.ensure_future(self.send_logs())

    async def handler(self, websocket, path):
        self.websocket = websocket
        #active_klines = asyncio.ensure_future(self.send_klines())
        consumer_task = asyncio.ensure_future(self.consumer())

        done, pending = await asyncio.wait([consumer_task])



    def run(self):
        print("Starting klines socket")

        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handler, 'localhost', 5678)
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()