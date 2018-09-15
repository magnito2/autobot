'''
lets try get cleaner once more.
lets use exceptions all through
'''

from threading import Thread
from binance.client import Client
from .exceptions import *
import time
from binance.exceptions import BinanceAPIException, BinanceOrderMinAmountException, BinanceOrderException

import logging

logger = logging.getLogger("abc.third_bot")

class OrderClient(Thread):

    min_qnty = 0.000001
    _latest_price = {'symbol' : None, 'price' : 0, 'timestamp' : 0}  #

    def __init__(self, params):
        Thread.__init__(self)
        self.name = params['name']
        self.uuid = params['uuid']
        self.new_side = params['side']
        self.SYMBOL = params['symbol']
        self.rest_api = Client(params['API_KEY'], params['API_SECRET'])
        self.keep_running = True

    def run(self):

        trade_count = 0
        #removed check permission, because it calls same API as get balance, it will be checked during that call

        while self.keep_running:
            try:

                if self.new_side == "BUY":  #lets find out is it is BTC or USDT we need to get balance of
                    asset = self.SYMBOL[3:]
                elif self.new_side == "SELL":
                    asset = self.SYMBOL[:3]
                else:
                    raise FatalError('side not set, either BUY or SELL')

                asset_balance = self.get_account_balance(asset)
                logger.debug(f"{self.name} fetched balance, {asset_balance}")
                #removed call to min quantity, call might be necessary later when multiple pairs are added.
                min_qnty = self.min_qnty
                if self.new_side == "BUY":
                    min_qnty = self.min_qnty * self.latest_price

                if asset_balance * 0.999 < min_qnty:
                    #this is naturally where we end our trade, report that trade is complete.
                    logger.info(f"{self.name} trade has completed successfully")
                    break

                if self.new_side == "BUY":
                    amount = (asset_balance / self.latest_price) * 0.995 ** (trade_count + 1)
                    logger.debug(f"[+]{self.name} Buying {amount}")
                    self.do_buy(amount)

                elif self.new_side == "SELL":
                    amount = asset_balance * (0.998 ** (trade_count + 1))
                    logger.debug(f"[+]{self.name} Selling {amount}")
                    self.do_sell(amount)

            except FatalError as e:
                logger.error(f"{self.name} fatal, {e.message}")
                break
            except ZeroDepositError as e:
                logger.error(f"{self.name}, {e.message}")
                break
            except BinanceAPIException as e:
                if int(e.code) in [-2010, -1010, -2011]:
                    logger.info(f"{self.name}, {e.message}")
                elif int(e.code) == -1013:
                    #balance below minimum allowable, should get here if we checking balances, end trade
                    logger.info(f"{self.name} cannot {self.new_side} less than minimum, {e.message}")
                    break
                elif int(e.code) == -2015:
                    logger.error(f"{self.name} {e.message}, exiting")
                    break
                elif int(e.status_code) == 429:
                    logger.warning(f"{self.name} hit a rate limit, backing dowm for 1 minute")
                    time.sleep(60)
                elif int(e.status_code) == 418:
                    logger.error(f"{self.name} Ooops, IP has been auto banned")
                    break
                else:
                    logger.error(f"{self.name} uncaught API exception, {e.message}, {e.code}, {e.status_code}")

            except Exception as e: #default, for all uncaught exceptions.
                logger.error(f"{self.name} Exceptiion, {e}")
                break

            if trade_count > 9:
                logger.info(f"{self.name} Exhausted the number of loops, which is {trade_count}, exiting")
                break

            trade_count += 1

    def get_account_balance(self, asset):
        try:
            account_info = self.rest_api.get_account()
        except Exception as e:
            raise e
        if not account_info['canTrade']:
            logger.error(f"{self.name} cannot trade")
            raise PermissionsError()
        balance_list = [x for x in account_info['balances'] if x['asset'] == asset]
        if not balance_list:
            raise ZeroDepositError()

        balance = balance_list[0]
        return float(balance['free'])

    @property
    def latest_price(self):
        if self._latest_price['symbol'] == self.SYMBOL and self._latest_price['timestamp'] - time.time() < 5:
            if self._latest_price['price']:
                return self._latest_price['price']
        price_dict = self.rest_api.get_symbol_ticker(symbol=self.SYMBOL)
        self._latest_price = {'symbol' : self.SYMBOL, 'timestamp' : time.time(), 'price' : float(price_dict['price']) }
        return self._latest_price['price']

    def do_buy(self, amount):
        logger.info(f"[*]{self.name} Buying {amount}")
        order = self.rest_api.order_market_buy(symbol=self.SYMBOL,quantity="{0:8f}".format(amount))

        logger.info("[+]{} Order successful, ID: {}".format(self.name, order['orderId']))
        return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order['orderId']}

    def do_sell(self, amount):
        logger.info(f"[*]{self.name} Selling {amount}")
        order = self.rest_api.order_market_sell(symbol=self.SYMBOL, quantity="{0:8f}".format(amount))

        logger.info("[+]{} Order successful, ID: {}".format(self.name, order['orderId']))
        return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order['orderId']}