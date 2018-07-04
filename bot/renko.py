from binance.client import BinanceRESTAPI
from playsound import playsound
import os, sys
from colorama import init, Fore
import threading

import logging
logger = logging.getLogger("RENKO")

class Renko(threading.Thread):

    def __init__(self, config):
        threading.Thread.__init__(self)
        init(autoreset=True)

        self.price_just_dropped = False
        self.price_just_rose = False
        self.last_order = None
        self.up_trend = None
        self.down_trend = None

        self.brick_size = float(config['brick_size'])
        self.symbol = config['symbol']
        self.time_frame = config['time_frame']

        self.bricks = []
        self.klines = []
        self.kline_event = threading.Event()
        self.trade_event_subscribers = []

        self.client = BinanceRESTAPI()
        self.trade_event = threading.Event()

        self.silence = False

    def play_rise_sound(self):
        try:
            playsound('sounds\\up.mp3', block=False)
        except Exception as e:
            logger.error(str(e))

    def play_fall_sound(self):
        try:
            playsound('sounds\\down.mp3', block=False)
        except Exception as e:
            logger.error(str(e))

    def run(self):
        '''
        main loop, checks for new klines and calls update renko
        :return: None
        '''

        historical_klines = self.get_historical_klines()
        if historical_klines:
            for kline in historical_klines:
                self.create_renko_bricks(kline, historical=True)

        print(Fore.YELLOW + "[+] Starting {} socket at an time interval of {} ".format(self.symbol, self.time_frame))
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

        print(Fore.YELLOW + "[+] Current trend is {} and the last bricks are {}".format(trend, self.bricks))
        logger.info("Interval {}, Start Price {}, Brick Size {}, Start Trend {}".format(self.time_frame, self.bricks[-1], self.brick_size, trend))
        # @todo: attempt the last trade on the position you are holding
        #ensure trade actually occured:
        # add a flag to hold last trade. if sell, or buy, reset it after reading, retry every x secs
        # and check if trend reversed before retry.
        while True:
            try:
                self.kline_event.wait()
                if self.klines:
                    kline = self.klines.pop(0)
                    self.latest_price = float(kline.close)
                    self.create_renko_bricks(kline)
                    if self.price_just_dropped or self.price_just_rose and abs(self.bricks[-1] - self.latest_price) > 0.1 * self.brick_size:
                        for subscriber in self.trade_event_subscribers:
                            subscriber.trade_event.set()
                            subscriber.price_just_rose = self.price_just_rose
                            subscriber.price_just_dropped = self.price_just_dropped
                        print(Fore.LIGHTRED_EX + "Set the trade event")
                        self.price_just_dropped = False
                        self.price_just_rose = False
                else:
                    self.kline_event.clear()
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
                logger.debug("[*] Final Brick Price: {}".format(current_price))

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
                        logger.info("[Up] price up. new brick at: {}".format(last_brick))
                        if not self.up_trend:
                            self.play_rise_sound()
                            self.price_just_rose = True
                            self.price_just_dropped = False
                            up_trend_factor = 1 #this factor should only be 2 for the reversal brick, all other bricks 1
                        else:
                            print(Fore.CYAN + "Price continuing to rise up")
                            logger.info("Price continuing to rise up")
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
                        logger.info("[Down] Price down. new brick at: {}".format(last_brick))
                        if not self.down_trend:
                            self.play_fall_sound()
                            self.price_just_dropped = True
                            self.price_just_rose = False
                            down_trend_factor = 1 #this factor should be 2 only for the reversal brick, all other bricks 1
                        else:
                            print(Fore.CYAN + "Price continuing to drop down")
                            logger.info("Price continuing to drop down")
                    self.down_trend = True
                    self.up_trend = False

            if len(self.bricks) > 20:
                self.bricks = self.bricks[-20:] #to avoid very long array, lets keep the last 20 values only

    def get_historical_klines(self):
        last_klines = self.client.klines(symbol=self.symbol, interval=self.time_frame)
        return last_klines

    def __del__(self):
        print("[!] Main exiting")