'''
chief
'''

from bot.new_klines_feeder import BinanceKlines
from bot.new_orders import Orders
from bot.new_renko import Renko
from bot.signaller import Signaller
from threading import Event, Thread
import logging

import os, sys

logger = logging.getLogger('renko.master')

class Master(Thread):
    '''
    Okay, I'll just be sitting over here waiting to be instructed to create a new bot
    '''
    BOTS_LIST = []
    RUNNING_KLINES = {}
    kline_event = Event()
    klines = []
    SYMBOL = None
    TIME_FRAME = None
    BRICK_SIZE = None
    kline_feeder = None
    keep_running = True
    renko_calculator = None
    signaller = None


    def __init__(self):
        Thread.__init__(self)

    def set_configurations(self, parameters):
        self.SYMBOL = parameters['symbol']
        self.TIME_FRAME = parameters['time_frame']
        self.BRICK_SIZE = float(parameters['brick_size'])
        #self.SMA_WINDOW = int(parameters['sma'])
        self.ztl_resolution = float(parameters['ztl_resolution'])

        renko_config = {'brick_size': self.BRICK_SIZE,'ztl_res' : self.ztl_resolution}
        signal_config = {'symbol': self.SYMBOL, 'time_frame': self.TIME_FRAME}
        self.renko_calculator = Renko(renko_config)
        self.signaller = Signaller(self.renko_calculator, signal_config)
        self.renko_calculator.signaller = self.signaller  # needed for only get_historical_klines
        self.kline_feeder = BinanceKlines(self.SYMBOL, self.TIME_FRAME, [self.renko_calculator])
        self.kline_feeder.start()

        self.renko_calculator.start()
        self.signaller.start()

    def create_new_bot(self, parameters):
        '''
        it will be a very good idea to check the bot's configs, you dont want a disaster
        :param parameters: API_KEY, API_SECRET
        :return:
        '''
        #create a bot listening to the klines_feeder
        logger.info("[+] Creating a new bot.")
        params = parameters
        params['symbol'] = self.SYMBOL
        print("[*] Inherited parameters")
        new_bot = Orders(self.signaller, params)
        self.signaller.trade_event_subscribers.append(new_bot)
        new_bot.start()
        self.BOTS_LIST.append(new_bot)
        print (f"All current bots are {self.BOTS_LIST}")

    def gracefully_end_all_trades(self):
        for bot in self.BOTS_LIST:
            bot.gracefully_end_trade()
        for bot in self.BOTS_LIST:
            bot.join(timeout = 60)
        timed_out_bots = []
        for bot in self.BOTS_LIST:
            if bot.is_alive():
                timed_out_bots.append(bot)
        logger.info(f"trades ended gracefully except for {[bot.name for bot in timed_out_bots]}")



    def run(self):
        '''
        lets listen for commands to create a new bot
        :return:
        '''
        print("running master")

    def restart(self):
        os.execv(sys.executable, ['python'] + sys.argv)

    def __del__(self):
        self.kline_feeder.keep_running = False
        self.renko_calculator.keep_running = False
        self.signaller.keep_running = False
        for bot in self.BOTS_LIST:
            bot.keep_running = False