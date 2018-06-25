from binance.client import BinanceRESTAPI
from colorama import Fore, init
from custom_client import CustomClient
import time
from threading import Thread

import logging
logger = logging.getLogger('orders')


class Orders(Thread):

    def __init__(self, params, renko_client):
        Thread.__init__(self)
        self.rest_api = CustomClient(params['API_KEY'], params['API_SECRET'])
        self.symbol = params['symbol']
        init(autoreset=True)
        self.renko_bot = renko_client

    # todo move order logic to this script, create a function to manage the orders
    # if an order is placed, try it five times, until if succeeds,
    # if not, give a good error notification.

    def create_buy_order(self, buy_price, trade_count=1):
        balance = float(self._get_account_balance(self.symbol[3:]))
        if balance:
            quantity_to_buy = (balance/buy_price) * pow(0.999, trade_count)
            if quantity_to_buy < self.get_min_qnty():
                print("Account balance lower that limit")
                return True
            print(Fore.CYAN + "[+] Creating a buy order for {} : {}".format(self.symbol, quantity_to_buy))
            self.logger.info("[+] Creating a buy order for {} : {}".format(self.symbol, quantity_to_buy))
            try:
                order = self.rest_api.new_order(symbol=self.symbol, side="BUY", type="MARKET", quantity="{0:8f}".format(quantity_to_buy), recv_window="10000")
                print(Fore.GREEN + "[+] Order successful, ID: {}".format(order.id))
                self.logger.info(Fore.GREEN + "[+] Order successful, ID: {}".format(order.id))
                return True
            except Exception as e:
                print(Fore.RED + str(e))
                self.logger.error("[!] " + str(e))

        else:
            print(Fore.RED + "[!] Not sufficient account balance")
            self.logger.error("[!] Not sufficient account balance")
        return False

    def create_sell_order(self, trade_count=1):
        balance = float(self._get_account_balance(self.symbol[:3]))
        if balance > self.get_min_qnty():
            quantity_to_sell = balance * pow(0.999, trade_count)
            if quantity_to_sell < self.get_min_qnty():
                print("Balance is lower than limit")
                return True
            print(Fore.RED + "[+] Creating a sell order for {} : {}".format(self.symbol, quantity_to_sell))
            self.logger.info("[+] Creating a sell order for {} : {}".format(self.symbol, quantity_to_sell))
            try:
                order = self.rest_api.new_order(symbol=self.symbol, side="SELL", type="MARKET", quantity="{0:8f}".format(quantity_to_sell), recv_window="10000")
                print(Fore.GREEN + "[+] Order successful, ID: {}".format(order.id))
                self.logger.info(Fore.GREEN + "[+] Order successful, ID: {}".format(order.id))
                return True
            except Exception as e:
                print(Fore.RED + str(e))
                self.logger.error("[!] " + str(e))
        else:
            print(Fore.RED + "[!] Not sufficient account balance")
            self.logger.error("[!] Not sufficient account balance")
        return False

    def _get_account_balance(self, asset):
        account_info = self.rest_api.account(recv_window="10000")
        balance = [x for x in account_info.balances if x.asset == asset][0]
        return balance.free

    def print_account_info(self):
        # print a few important details about the user's account
        info = self.rest_api.account()
        print(Fore.BLUE + "-------ACCOUNT INFORMATION--------")
        print(Fore.BLUE + "Account balances:")
        for bal in info.balances:
            if float(bal.free) > 0:
                print(Fore.YELLOW + "{} : {}".format(bal['asset'], bal['free']))
        print("---------------------------------------")

    def get_min_qnty(self):
        exch_inf_api = CustomClient()
        ex_inf = exch_inf_api.exchange_info()

        if not ex_inf.symbols:
            raise ValueError("incorrent data back")
        current_symbol = [x for x in ex_inf.symbols if x['symbol'] == self.symbol]
        if current_symbol:
            current_symbol = current_symbol[0]
            lot_size = [x for x in current_symbol['filters'] if x['filterType'] == 'LOT_SIZE']
            if lot_size:
                lot_size = lot_size[0]
                min_qnty = lot_size['minQty']
                return float(min_qnty)
            else:
                raise ValueError("property LOT_SIZE is missing")
        else:
            pass

    def do_create_orders(self):

        count_attempts = 1
        while True:
            self.renko_bot.trade_event.wait() #wait for notification that its time to create an order
            print("placing order")

            current_price = self.renko_bot.latest_price
            last_brick = self.renko_bot.bricks[-1]
            if self.renko_bot.price_just_dropped and self.renko_bot.price_just_rose:
                self.logger.error("you cannot have both price_just_rose and price_just_dropped set, it dangerous")
                print(Fore.RED + "you cannot have both price_just_rose and price_just_dropped set, it dangerous")
            elif self.renko_bot.price_just_rose:  # only trigger buy during the first brick after reversal + 5 pips
                if current_price - last_brick >= 0.1 * self.renko_bot.brick_size or self.config.first_trade:  # assuming a brick size of 50, 5 pips, if brick size changes, value changes
                    print(Fore.MAGENTA + "[+] creating a buy order")
                    self.logger.info("[+] Creating a buy order")
                    if self.create_buy_order(current_price, trade_count=count_attempts):
                        self.renko_bot.price_just_rose = False
                        self.renko_bot.trade_event.clear()
            elif self.renko_bot.price_just_dropped:  # only trigger sell during the first brick after reversal
                if last_brick - current_price >= 0.1 * self.renko_bot.brick_size or self.config.first_trade:
                    print(Fore.MAGENTA + "[-] creating a sell order")
                    self.logger.info("[-] Creating a sell order")
                    if self.create_sell_order(trade_count=count_attempts):
                        self.renko_bot.price_just_dropped = False
                        self.renko_bot.trade_event.clear()
            if not self.renko_bot.trade_event.is_set():
                print(Fore.LIGHTYELLOW_EX + "Cleared trade event")
            else:
                count_attempts += 1
            if count_attempts > 5:
                print("Failed to trade correctly")
                self.renko_bot.trade_event.clear()
                count_attempts = 1
                self.renko_bot.price_just_dropped = False
                self.renko_bot.price_just_rose = False

            if self.config.first_trade:
                self.config.first_trade = False


    def run(self):
        print(Fore.YELLOW + "Starting order factory")
        self.do_create_orders()

