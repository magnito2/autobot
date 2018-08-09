'''
the boss, you need someone to just holla, buy, sell
'''

from .klines import Klines
from .coin import BitCoin, USDT
from .renko_calculator import Renko
from .order import Order
from .account import Account

import threading
import logging

logger = logging.getLogger('backtest.trader')

class Trader:

    def __init__(self, config):
        self.klines_feeder = Klines(config)
        self.renko_calculator = Renko(config)
        self.account = Account(1)
        self.orders = Order(self.account)
        self.sma_window = config['SMA']
        self.limit = config['limit']
        self.time_frame = config['time_frame']
        self.trade_event_subscribers = []

    def run(self):
        logger.info("lets start off with a prayer.;)")
        historical_klines = self.klines_feeder.get_historical_klines(limit=self.klines_feeder.get_limit_count(self.limit, self.time_frame))
        for kline in historical_klines:
            new_brick = self.renko_calculator.create_renko_bricks(kline)
            if not new_brick:
                continue
            if not len(self.renko_calculator.bricks) > self.sma_window:
                continue
            sma = self.renko_calculator.get_sma(new_brick)

            if new_brick.price < sma:
                logger.info("[+] Signalling a sell")
                self.orders.sell(kline)

            elif new_brick.price > sma:
                logger.info("[+] Signalling a buy")
                self.orders.buy(kline)
        logger.info("finalizing the trade")
        last_kline = historical_klines[-1]
        self.orders.buy(last_kline)

        logger.info("Backtesting has been completed.")
        logger.info("Reporting")
        logger.info(f"BTC Balance {self.account.bitcoin.balance()}")
        logger.info(f"USDT Balance {self.account.usdt.balance()}")


