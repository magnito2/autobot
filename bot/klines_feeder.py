'''
same same a before, for now
'''

from binance.client import BinanceWebSocketAPI, BinanceRESTAPI
from threading import Thread,Event
import time, logging

logger = logging.getLogger("renko.klines")

class BinanceKlines(Thread):

    def __init__(self, symbol, interval, subscribers):
        Thread.__init__(self)
        self.symbol = symbol
        self.interval = interval
        self.subscribers = subscribers
        self.ws_client = BinanceWebSocketAPI()
        self.rest_client = BinanceRESTAPI()
        self.keep_running = True
        self.restart_count = 1

    def run(self):
        while self.keep_running:
            self.ws_client.kline(symbol = self.symbol, interval = self.interval, callback=self.on_message)
            sleep = 30 * self.restart_count
            logger.error("socket was closed, reconnecting in {} seconds".format(sleep))
            time.sleep(sleep)
            self.restart_count += 1
        self.ws_client = None

    def on_message(self, kline):
        #to recieve notifications, subscibers should have an array called klines and an event called kline_event
        for subscriber in self.subscribers:
            subscriber.klines.append(kline)
            subscriber.kline_event.set()

    def __del__(self):
        self.ws_client = None
        logger.info("Klines stopping")