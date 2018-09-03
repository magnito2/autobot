'''
simple job, just know when conditions are right and shout "buy" or "sell"
'''

import threading
import logging
from binance.client import Client
from datetime import datetime
from bot.models import Candlestick

logger = logging.getLogger("renko.Signaller")

class Signaller(threading.Thread):

    def __init__(self, renko_calculator, config):
        threading.Thread.__init__(self)
        self.renko_calculator = renko_calculator
        self.keep_running = True
        self.renko_event = threading.Event()
        self.trade_event_subscribers = []

        self.rest_api = Client(None, None)
        self.symbol = config['symbol']
        self.time_frame = config['time_frame']
        self.name = "Signaller"
        self.indicator = 'ZTL'
        self.last_signal = None

    def run(self):
        '''
        this function now has to populate both renko_calculator and SMA_calculator
        :return:
        '''

        logger.debug("Waiting for renko calculator to be ready")
        self.renko_calculator.ready.wait()

        self.latest_price = self.renko_calculator.latest_price

        self.auto_trade()

    def signal(self, side):
        '''
        Subscribers are instances of new_order class. the subscribers should have
        1. trade_event, event to wait for.
        2. new_side = either buy or sell
        :param side:
        :return:
        '''
        print(f"telling everyone to {side}")
        for subscriber in self.trade_event_subscribers:
            subscriber.new_side = side
            subscriber.trade_event.set()
        self.last_signal = side

    def get_historical_klines(self, startTime=None, endTime=None, limit=None):
        hist_klines = []
        while len(hist_klines) < limit:
            raw_last_klines = self.rest_api.get_klines(symbol = self.symbol, interval=self.time_frame, startTime=startTime, endTime=endTime, limit=limit)
            last_klines = [Candlestick.object_from_dictionary(entry) for entry in raw_last_klines]
            hist_klines = last_klines + hist_klines
            endTime = hist_klines[0].open_time
            logger.debug(f"[+] fetching upto {endTime}")
            print(f"[+] fetching upto {endTime}")
        return hist_klines

    def __del__(self):
        logger.error(f"[!] {self.name} is exiting")

    def auto_trade(self):

        last_brick = self.renko_calculator.bricks[-1]

        ztl = self.renko_calculator.get_last_ztl()
        if last_brick.price < ztl:
            logger.info("[+] Signalling a sell")
            self.signal("SELL")
        elif last_brick.price > ztl:
            logger.info("[+] Signalling a buy")
            self.signal("BUY")

        while self.keep_running:
            self.renko_event.wait()
            logger.info(f"[+] new brick {self.renko_calculator.bricks[-1].price}")

            trend = self.renko_calculator.trend
            latest_brick = self.renko_calculator.bricks[-1]
            self.latest_price = self.renko_calculator.latest_price
            latest_ztl = self.renko_calculator.get_last_ztl()
            if trend == "UP":
                if latest_ztl < latest_brick.price:
                    logger.info("[+] Buy time")
                    self.signal('BUY')
            elif trend == "DOWN":
                if latest_ztl > latest_brick.price:
                    logger.info("[+] Sell time")
                    self.signal('SELL')
            self.renko_event.clear()
            self.last_trend = trend


    def manual_trade(self):

        while self.keep_running:
            self.manual_trade_event.wait()




