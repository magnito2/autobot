from settings import *
from binance.client import BinanceRESTAPI
from playsound import playsound
import os, sys
from os.path import getmtime
from colorama import init, Fore
import threading

class Renko(threading.Thread):

    def __init__(self, logger, config, silent=False):
        threading.Thread.__init__(self)
        init(autoreset=True)
        self.price_just_dropped = False
        self.price_just_rose = False
        self.last_order = None
        self.silence = silent #dont show anything weird on restart
        self.trade_event = threading.Event()
        self.logger = logger
        self.config = config
        self.brick_size = config.brick_size
        self.klines = []
        self.kline_event = threading.Event()

        self.client = BinanceRESTAPI(API_KEY, API_SECRET)
        self.bricks = []
        self.brick_size = 0
        self.WATCHED_FILES = ['config.ini']  # when a change occurs to any of this files, the bot is restarted
        self.WATCHED_FILES_MTIMES = [(f, getmtime(f)) for f in self.WATCHED_FILES]
        self.up_trend = None
        self.down_trend = None
        self.logger = None
        self.config = None

        self.keep_running = True

    def play_rise_sound(self):
        try:
            playsound('sounds\\up.mp3', block=False)
        except Exception as e:
            self.logger.error(str(e))

    def play_fall_sound(self):
        try:
            playsound('sounds\\down.mp3', block=False)
        except Exception as e:
            self.logger.error(str(e))

    def run(self):
        '''
        main loop, checks for new klines and calls update renko
        :return: None
        '''

        if not self.silence:
            self.print_account_info()

        historical_klines = self.get_historical_klines()
        if historical_klines:
            for kline in historical_klines:
                self.create_renko_bricks(kline, historical=True)

        print(Fore.YELLOW + "[+] Starting {} socket at an time interval of {} ".format(self.config.symbol, self.config.time_frame))
        print(Fore.YELLOW + "[+] Starting Price {}, Brick Size {}".format(self.bricks[-1], self.brick_size))

        trend = None
        if self.up_trend:
            trend = "[Up]"
            self.price_just_rose = True
        if self.down_trend:
            trend = "[Down]"
            self.price_just_dropped = True
        if self.up_trend and self.down_trend:
            trend = "[Confusion]"

        if self.up_trend or self.down_trend:
            print(Fore.LIGHTYELLOW_EX + "Establishing initial conditions")
            if self.klines:
                self.latest_price = float(self.klines[-1].close)
            else:
                self.latest_price = self.bricks[-1]
            self.config.first_trade = True
            self.trade_event.set() #establish initial position, buy if not bought, sell if not sold.

        print(Fore.YELLOW + "[+] Current trend is {} and the last bricks are {}".format(trend, self.bricks))
        self.logger.info("Interval {}, Start Price {}, Brick Size {}, Start Trend {}".format(self.config.time_frame, self.bricks[-1], self.brick_size, trend))
        # @todo: attempt the last trade on the position you are holding
        #ensure trade actually occured:
        # add a flag to hold last trade. if sell, or buy, reset it after reading, retry every x secs
        # and check if trend reversed before retry.
        while self.keep_running:
            try:
                self.kline_event.wait()
                if self.klines:
                    kline = self.klines.pop(0)
                    self.latest_price = float(kline.close)
                    self.create_renko_bricks(kline)
                    if self.price_just_dropped or self.price_just_rose and not self.trade_event.is_set() and abs(self.bricks[-1] - self.latest_price) > 0.1 * self.brick_size:
                        self.trade_event.set()
                        print(Fore.LIGHTRED_EX + "Set the trade event")
                else:
                    self.kline_event.clear()
                self.reload_config()
            except KeyboardInterrupt:
                break


    def create_renko_bricks(self, kline, historical = False):

        current_price = float(kline.close)

        if not historical:
            if not kline.is_final:
                print("[+] {} Current Price: {}".format(kline.end_time, current_price))
                return
            else:
                print(Fore.BLUE + "[+] Final Brick Price: {}".format(current_price))
                self.logger.debug("[*] Final Brick Price: {}".format(current_price))

        if len(self.bricks) == 0:
            self.bricks.append(current_price - (current_price % self.brick_size)) #round off to the last brick size

        else:
            last_brick = self.bricks[-1]
            if self.up_trend:
                up_trend_factor = 1  #this is the actual travel distance of a price to reverse the brick
            else:
                up_trend_factor = 2
            if self.down_trend:
                down_trend_factor = 1
            else:
                down_trend_factor = 2

            if current_price - last_brick >= self.brick_size * up_trend_factor:
                while current_price - last_brick >= self.brick_size * up_trend_factor:
                    next_brick = last_brick + self.brick_size * up_trend_factor
                    self.bricks.append(next_brick)
                    last_brick = self.bricks[-1]
                    if not historical: #this helps in loading historic renkos silently.
                        print()
                        print(Fore.GREEN + "[Up] price up. new brick at: {}".format(last_brick))
                        self.logger.info("[Up] price up. new brick at: {}".format(last_brick))
                        if not self.up_trend:
                            self.play_rise_sound()
                            self.price_just_rose = True
                            self.price_just_dropped = False
                            up_trend_factor = 1 #this factor should only be 2 for the reversal brick, all other bricks 1
                        else:
                            print(Fore.CYAN + "Price continuing to rise up")
                            self.logger.info("Price continuing to rise up")
                    self.up_trend = True
                    self.down_trend = False

            elif last_brick - current_price >= self.brick_size * down_trend_factor:
                while last_brick - current_price >= self.brick_size * down_trend_factor:
                    next_brick = last_brick - self.brick_size * down_trend_factor
                    self.bricks.append(next_brick)
                    last_brick = self.bricks[-1]
                    if not historical: #data is not historical
                        print()
                        print(Fore.RED + "[Down] Price down. new brick at: {}".format(last_brick))
                        self.logger.info("[Down] Price down. new brick at: {}".format(last_brick))
                        if not self.down_trend:
                            self.play_fall_sound()
                            self.price_just_dropped = True
                            self.price_just_rose = False
                            down_trend_factor = 1 #this factor should be 2 only for the reversal brick, all other bricks 1
                        else:
                            print(Fore.CYAN + "Price continuing to drop down")
                            self.logger.info("Price continuing to drop down")
                    self.down_trend = True
                    self.up_trend = False

            if len(self.bricks) > 20:
                self.bricks = self.bricks[-20:] #to avoid very long array, lets keep the last 20 values only

    def print_account_info(self):
        # print a few important details about the user's account
        info = self.client.account(recv_window="10000")
        print(Fore.BLUE + "-------ACCOUNT INFORMATION--------")
        print(Fore.BLUE + "Account balances:")
        for bal in info.balances:
            if float(bal.free) > 0:
                print(Fore.YELLOW + "{} : {}".format(bal.asset, bal.free))
        print("---------------------------------------")

    def reload_config(self, force = False):
        for f, mtime in self.WATCHED_FILES_MTIMES:
            if getmtime(f) != mtime:
                print(Fore.YELLOW + "[*] Configuration changed, reloading...")
                self.logger.info("[*] Configuration changed, reloading...")
                os.execv(sys.executable, ['python'] + sys.argv)
                self.WATCHED_FILES_MTIMES = [(f, getmtime(f)) for f in self.WATCHED_FILES]
            elif force:
                print(Fore.YELLOW + "Reloading bot")
                os.execv(sys.executable, ['python'] + sys.argv)

    def get_historical_klines(self):
        last_klines = self.client.klines(symbol=self.config.symbol, interval=self.config.time_frame)
        return last_klines

    def __del__(self):
        print("[!] Main exiting")