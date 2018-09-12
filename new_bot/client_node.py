'''
individual client nodes. runs under the bot manager.
should only holder client specific code.
only task, buy/sell.
should report on everything needed about a client,
retrieve complete client data from binance.
'''
from threading import Thread
from binance.client import Client
import logging
import time

logger = logging.getLogger("abc.client_node")
logger.setLevel(logging.DEBUG)

class ClientNode(Thread):
    min_qnty = 0

    def __init__(self, params):
        Thread.__init__(self)
        self.pending_orders = []
        self.rest_api = Client(params['API_KEY'], params['API_SECRET'])
        self.SYMBOL = params['symbol']
        self.keep_running = True
        self.new_side = params['side']

        self.uuid = params['uuid']
        self.name = params['name']
        print(f"[+] Bot name is {self.name}")

    def run(self):

        sleep_time = 0
        trade_count = 0
        error_count = 0

        rv = self._check_permissions()
        if not rv['status']: #bots that have permission issues get terminated here
            logger.debug(f"{self.name} API KEY has permission errors, check key can trade and get account balance")
            #logger.error(f"{self.name} {rv['exception']}")
            return

        while self.keep_running:

            if error_count > 10:
                logger.info(f"{self.name} too many errors, check logs, goodbye!!")
                break

            logger.debug(f"{self.name} sleeping for {sleep_time}")
            time.sleep(sleep_time) #sleep time is determined by the different events.
            sleep_time = 0 #to avoid unnecessary sleep next time.

            asset = None
            if self.new_side == "BUY":
                asset = self.SYMBOL[3:]
            elif self.new_side == "SELL":
                asset = self.SYMBOL[:3]
            else:
                raise ValueError('side not set, either BUY or SELL')

            account_resp = self._get_account_balance(asset)
            if not account_resp['status']:
                #report back to master the error encountered
                if account_resp['exception'].code == -1021:
                    #we got ourselves a juicy little Timestamp for this request is outside of the recvWindow.
                    logger.error(f"{self.name} timestamp error getting balance {account_resp['exception'].code}, {account_resp['exception']}")
                elif account_resp['exception'].code == -7000:
                    #logger.error(f"{self.name} free balance in account is zero: {account_resp['exception']}, exiting")
                    self.keep_running = False
                    break
                else:
                    logger.error(f"{self.name} error getting balance {account_resp['exception'].code}: {account_resp['exception']}")
                sleep_time = 5
                error_count += 1 #if it fails so many times, die
                continue
            asset_balance = float(account_resp['balance'])
            min_qnty = self.get_min_qnty()
            if self.new_side == "BUY":
                min_qnty = min_qnty * self.latest_price
            logger.debug(f"[+]{self.name} Minimum allowable {self.new_side.lower()} quantity is {min_qnty}")
            logger.debug(f"{self.name} Account balance for {asset} is {asset_balance}")
            if asset_balance * 0.999 < min_qnty:
                #this is naturally where we end our trade, report that trade is complete.
                logger.info(f"{self.name} trade has completed successfully")
                break

            if self.new_side == "BUY":
                amount = (asset_balance / self.latest_price) * 0.998 ** (trade_count + 1)
                logger.debug(f"[+]{self.name} Buying {amount}")
                order_resp = self.do_buy(amount)

            elif self.new_side == "SELL":
                amount = asset_balance * (0.998 ** (trade_count + 1))
                logger.debug(f"[+]{self.name} Selling {amount}")
                order_resp = self.do_sell(amount)
            else:
                continue

            if not order_resp['status']:
                if order_resp['exception'].code == -1021:
                    # we got ourselves a juicy little Timestamp for this request is outside of the recvWindow.
                    logger.error(f"{self.name} timestamp error, {order_resp['exception'].code}, {order_resp['exception'].message}")
                    sleep_time = 60
                elif order_resp['exception'].code in [-2010, -1010, -2011]:
                    # we got some processing error
                    logger.error(f"{self.name} {order_resp['exception'].code}, {order_resp['exception'].message}")
                    trade_count += 1
                    print(f"[*]{self.name} Current trade counts {trade_count}")
                elif order_resp['exception'].code == -7000:
                    #logger.error(f"{self.name} free balance in account is zero: {order_resp['exception'].message}, exiting")
                    break #this bot cannot make any trades, lets exit

                elif order_resp['exception'].code == -1013:
                    #occurs when quantity is below allowed, end trade here.
                    logger.debug(f"[*]{self.name} Ending trade with {amount} , {self.latest_price}")
                    break

            if trade_count > 20:
                logger.info(f"{self.name} trade failed to complete, aborting")
                break

    def do_buy(self, amount):
        try:
            logger.info(f"[*]{self.name} Buying {amount}")
            order = self.rest_api.order_market_buy(symbol=self.SYMBOL,quantity="{0:8f}".format(amount))

            logger.info("[+]{} Order successful, ID: {}".format(self.name, order['orderId']))
            return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order['orderId']}
        except Exception as e:
            #logger.error("[!] " + str(e))
            return {'status': False, 'exception': e}

    def do_sell(self, amount):
        try:
            logger.info(f"[*]{self.name} Selling {amount}")
            order = self.rest_api.order_market_sell(symbol=self.SYMBOL, quantity="{0:8f}".format(amount))
            logger.info("[+]{} Order successful, ID: {}".format(self.name, order['orderId']))
            return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order['orderId']}
        except Exception as e:
            #logger.error("[!] " + str(e))
            return {'status': False, 'exception': e}

    def _get_account_balance(self, asset):
        try:
            account_info = self.rest_api.get_account()
        except Exception as e:
            return {'status' : False, 'exception' : e}
        balance_list = [x for x in account_info['balances'] if x['asset'] == asset]
        if not balance_list:
            error = ValueError('The Free balance is Zero')

            error.code = -7000
            return {'status': False, 'exception': error}
        balance = balance_list[0]
        return {'status' : True, 'balance' : balance['free'] }

    def _get_open_orders(self):
        try:
            open_orders = self.rest_api.get_open_orders(symbol = self.SYMBOL)
        except Exception as e:
            return {'status' : False, 'exception' : e}
        return {'status' : True, 'open_orders' : open_orders}

    def get_min_qnty(self):

        if self.min_qnty:
            return self.min_qnty
        exch_inf_api = self.rest_api
        ex_inf = exch_inf_api.get_exchange_info()

        if not ex_inf['symbols']:
            #raise ValueError("incorrent data back")
            return 0
        current_symbol = [x for x in ex_inf['symbols'] if x['symbol'] == self.SYMBOL]
        if current_symbol:
            current_symbol = current_symbol[0]
            lot_size = [x for x in current_symbol['filters'] if x['filterType'] == 'LOT_SIZE']
            if lot_size:
                lot_size = lot_size[0]
                min_qnty = lot_size['minQty']
                self.min_qnty = float(min_qnty)
                return self.min_qnty
            else:
                #raise ValueError("property LOT_SIZE is missing")
                return 0
        else:
            pass

    def _check_permissions(self):
        try:
            #account_info = self.rest_api.get_account(recv_window="10000")
            account_info = self.rest_api.get_account()
        except Exception as e:
            return {'status' : False, 'exception' : e}
        if not account_info['canTrade']:
            return {'status' : False, 'exception' : ValueError('Permission needed to trade')}
        return {'status' : True}

    @property
    def latest_price(self):
        price_dict = self.rest_api.get_symbol_ticker(symbol=self.SYMBOL)
        print(price_dict)
        return float(price_dict['price'])
