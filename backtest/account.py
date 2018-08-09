from .coin import BitCoin, USDT

import logging

logger = logging.getLogger('backtest.account')

class Account:

    def __init__(self, BTC_amount):

        self.bitcoin = BitCoin()
        self.bitcoin.deposit(BTC_amount)
        self.usdt = USDT()
        self.fee = 0.001
        self.minimum_amount = 0.000001
        logger.info(f"Initializing the testing account with {self.bitcoin.balance()} BTC")

    def get_balance(self, asset):
        if asset == 'BTC':
            return self.bitcoin.balance()
        if asset == 'USDT':
            return self.usdt.balance()

    def buy(self, amount, price):
        cost = amount * price
        fee = cost * self.fee
        if self.usdt.balance() < cost + fee:
            raise ValueError('Buying more than you can afford, you should be able to pay for fees too')

        self.usdt.withdraw(cost + fee)
        self.bitcoin.deposit(amount)
        logger.info(f"buy order successful, amount {amount} for {cost}")

    def sell(self, amount, price):
        value = amount * price
        fee = amount * self.fee
        if self.bitcoin.balance() < amount + fee:
            raise ValueError('selling more than you own, you should be able to pay for fees too')

        self.bitcoin.withdraw(amount + fee)
        self.usdt.deposit(value)
        logger.info(f"sell order successful, amount {amount} for {value}")
