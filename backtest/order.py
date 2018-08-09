'''
the fake trader.  lol, recieves signals to buy and to sell (fake signals from a fake , naah, real renko)
'''

from .account import Account

import logging
logger=logging.getLogger('backtest.order')

class Order():

    def __init__(self, account):

        self.new_side = None
        self.keep_running = True
        self.account = account
        self.minimum_amount = 0.000001

    def buy(self, kline):
        #calculate how much to buy and throw a buy order to account
        price = float(kline.close)
        counter = 0
        while self.account.usdt.balance() > (self.minimum_amount * price):
            amount = (self.account.usdt.balance() / price) * 0.998
            try:
                logger.info(f"attempting a buy order {amount}")
                self.account.buy(amount, price)
            except Exception as e:
                print(e)
            if counter > 20:
                logger.error("Failed to complete trade successfully, exiting")
                break
            counter += 1

    def sell(self, kline):
        #calculate how much to sell and throw a sell order to account
        price = float(kline.close)
        counter = 0
        while self.account.bitcoin.balance() > self.minimum_amount:
            amount = self.account.bitcoin.balance() * 0.998
            try:
                logger.info(f"Attempting a sell order, amount {amount}")
                self.account.sell(amount, price)
            except Exception as e:
                print(e)
            if counter > 20:
                logger.error("Failed to complete trade successfully, exiting")
                break
            counter += 1
