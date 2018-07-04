'''
chief
'''

from bot.klines_feeder import BinanceKlines
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
        self.BRICK_SIZE = int(parameters['brick_size'])
        self.SMA_WINDOW = int(parameters['sma'])

        renko_config = {'brick_size': self.BRICK_SIZE, 'SMA': self.SMA_WINDOW}
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
        new_bot = Orders(self.signaller, params)
        self.BOTS_LIST.append(new_bot)
        self.signaller.trade_event_subscribers.append(new_bot)
        new_bot.start()

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