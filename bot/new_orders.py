from threading import Thread, Event
from bot.custom_client import CustomClient
import time
import logging
from binance.bind import BinanceClientError

logger = logging.getLogger("renko.orders")
logger.setLevel(logging.DEBUG)

class Orders(Thread):

    def __init__(self, Trade_Signaller, params):
        Thread.__init__(self)
        self.trade_event = Event()
        self.pending_orders = []
        self.trade_signal = Trade_Signaller
        self.rest_api = CustomClient(params['API_KEY'], params['API_SECRET'])
        self.SYMBOL = params['symbol']
        self.keep_running = True
        self.new_side = None

        self.uuid = params['uuid']
        print(f"[+] Bot UUID is {self.uuid}")
        self.name = params['name']
        print(f"[+] Bot name is {self.name}")

    def run(self):

        sleep_time = 0
        trade_count = 0
        error_count = 10

        if not self._check_permissions()['status']: #bots that have permission issues get terminated here
            logger.debug(f"{self.name} API KEY has permission errors, check key can trade and get account balance")
            return

        while self.keep_running:

            if error_count > 10:
                self.trade_event.clear()
                logger.info(f"{self.name} too many errors, check logs, goodbye!!")
                break

            logger.debug(f"{self.name} sleeping for {sleep_time}")
            time.sleep(sleep_time) #sleep time is determined by the different events.
            sleep_time = 0 #to avoid unnecessary sleep next time.

            self.trade_event.wait() #event is set from outside by renko class or another signaller

            orders_resp = self._get_open_orders() #if there are any open orders, don't proceed to place new ones
            if not orders_resp['status']:
                #report back to master the error encountered
                logger.error(f"[!]{self.name} Error getting orders : {orders_resp['exception']}")
                error_count += 1 #more drastic actions in future, coz this sometimes happen when a user deletes keys, locking us out.
                sleep_time = 10
                continue
            for open_order in orders_resp['open_orders']:
                logger.debug(f"[+]{self.name} Order status is: {open_order['status']}")
                if open_order['status'] == "ACTIVE":
                    sleep_time = 60
                    continue
            asset = None
            if self.new_side == "BUY":
                asset = self.SYMBOL[3:]
            elif self.new_side == "SELL":
                asset = self.SYMBOL[:3]
            account_resp = self._get_account_balance(asset)
            if not account_resp['status']:
                #report back to master the error encountered
                if account_resp['exception'].error_code == -1021:
                    #we got ourselves a juicy little Timestamp for this request is outside of the recvWindow.
                    logger.error(f"{self.name} timestamp error getting balance {account_resp['exception'].error_code}, {account_resp['exception'].error_message}")
                elif account_resp['exception'].error_code == -7000:
                    logger.error(f"{self.name} free balance in account is zero: {account_resp['exception'].error_message}, exiting")
                    break
                else:
                    logger.error(f"{self.name} error getting balance {account_resp['exception'].error_code}: {account_resp['exception'].error_code}")
                sleep_time = 5
                error_count += 1 #if it fails so many times, die
                continue
            asset_balance = float(account_resp['balance'])
            min_qnty = self.get_min_qnty()
            if self.new_side == "BUY":
                min_qnty = min_qnty * self.trade_signal.latest_price
            logger.debug(f"[+]{self.name} Minimum allowable {self.new_side.lower()} quantity is {min_qnty}")
            logger.debug(f"{self.name} Account balance for {asset} is {asset_balance}")
            if asset_balance * 0.999 < min_qnty:
                #this is naturally where we end our trade, report that trade is complete.
                self.trade_event.clear()
                logger.info(f"{self.name} trade has completed successfully")
                trade_count = 0
                continue

            self.latest_price = float(self.trade_signal.latest_price)
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
                if order_resp['exception'].error_code == -1021:
                    # we got ourselves a juicy little Timestamp for this request is outside of the recvWindow.
                    logger.error(f"{self.name} timestamp error, {order_resp['exception'].error_code}, {order_resp['exception'].error_message}")
                    sleep_time = 60
                elif order_resp['exception'].error_code in [-2010, -1010, -2011]:
                    # we got some processing error
                    logger.error(f"{self.name} {order_resp['exception'].error_code}, {order_resp['exception'].error_message}")
                    trade_count += 1
                    print(f"[*]{self.name} Current trade counts {trade_count}")
                elif account_resp['exception'].error_code == -7000:
                    logger.error(f"{self.name} free balance in account is zero: {account_resp['exception'].error_message}, exiting")
                    break #this bot cannot make any trades, lets exit

                elif order_resp['exception'].error_code == -1013:
                    #occurs when quantity is below allowed, end trade here.
                    logger.debug(f"[*]{self.name} Ending trade with {amount} , {self.latest_price}")
                    self.trade_event.clear()
                    trade_count = 0
                    continue

            if trade_count > 20:
                self.trade_event.clear()
                trade_count = 0
                logger.info(f"{self.name} trade failed to complete, aborting")

    def do_buy(self, amount):
        try:
            logger.info(f"[*]{self.name} Buying {amount}")
            order = self.rest_api.new_order(symbol=self.SYMBOL, side="BUY", type="MARKET",
                                            quantity="{0:8f}".format(amount), recv_window="10000")
            logger.info("[+]{} Order successful, ID: {}".format(self.name, order.id))
            return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order.id}
        except Exception as e:
            logger.error("[!] " + str(e))
            return {'status': False, 'exception': e}

    def do_sell(self, amount):
        try:
            logger.info(f"[*]{self.name} Selling {amount}")
            order = self.rest_api.new_order(symbol=self.SYMBOL, side="SELL", type="MARKET",
                                            quantity="{0:8f}".format(amount), recv_window="10000")
            logger.info("[+]{} Order successful, ID: {}".format(self.name, order.id))
            return {'status': True, 'exception': None, 'message': 'Order successful', 'orderID': order.id}
        except Exception as e:
            logger.error("[!] " + str(e))
            return {'status': False, 'exception': e}

    def _get_account_balance(self, asset):
        try:
            account_info = self.rest_api.account(recv_window="10000")
        except Exception as e:
            return {'status' : False, 'exception' : e}
        balance_list = [x for x in account_info.balances if x.asset == asset]
        if not balance_list:
            error = BinanceClientError('The Free balance is Zero')
            error.error_code = -7000
            return {'status': False, 'exception': error}
        balance = balance_list[0]
        return {'status' : True, 'balance' : balance.free }

    def _get_open_orders(self):
        try:
            open_orders = self.rest_api.current_open_orders(self.SYMBOL)
        except Exception as e:
            return {'status' : False, 'exception' : e}
        return {'status' : True, 'open_orders' : open_orders}

    def get_min_qnty(self):
        exch_inf_api = CustomClient()
        ex_inf = exch_inf_api.exchange_info()

        if not ex_inf.symbols:
            #raise ValueError("incorrent data back")
            return 0
        current_symbol = [x for x in ex_inf.symbols if x['symbol'] == self.SYMBOL]
        if current_symbol:
            current_symbol = current_symbol[0]
            lot_size = [x for x in current_symbol['filters'] if x['filterType'] == 'LOT_SIZE']
            if lot_size:
                lot_size = lot_size[0]
                min_qnty = lot_size['minQty']
                return float(min_qnty)
            else:
                #raise ValueError("property LOT_SIZE is missing")
                return 0
        else:
            pass

    def gracefully_end_trade(self):
        '''
        End the trade properly (convert the coins back to their oroginal format.
        For now, coins will be converted to BTC, in future, users can choose which pair they prefer.
        Trades can end when
            1. Account expires
            2. A new trading pair is selected
            3. Use ends the trade (ask user to end trade in case he/she plans to delete keys)
        :return:
        '''
        if self.SYMBOL[:3] == "BTC":
            #happens only in BTCUSDT, btc is the base currency, USDT is the quote currency.
            logger.info(f"{self.name} Closing the trade, buying back BTC")
            self.new_side = "BUY"
            self.trade_event.set()
        elif self.SYMBOL[3:] == "BTC":
            #all other pairs of trading
            logger.info(f"{self.name} Closing the trading, selling all {self.SYMBOL[:3]}")
            self.new_side = "SELL"
            self.trade_event.set()

    def _check_permissions(self):
        try:
            account_info = self.rest_api.account(recv_window="10000")
        except Exception as e:
            return {'status' : False, 'exception' : e}
        if not account_info.can_trade:
            return {'status' : False, 'exception' : ValueError('Permission needed to trade')}
        return {'status' : True}
