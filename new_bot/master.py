'''
chief
'''

from .klines_feeder import BinanceKlines
from .renko_calculator import Renko
from .signaller import Signaller
from .bot_manager import Manager
from threading import Event, Thread
import logging

logger = logging.getLogger('abc.Master')

class Master(Thread):
    '''
    Okay, I'll just be sitting over here waiting to be instructed to create a new bot
    '''
    SYMBOL = None
    TIME_FRAME = None
    BRICK_SIZE = None
    kline_feeder = None
    keep_running = True
    renko_calculator = None
    signaller = None

    def __init__(self):
        Thread.__init__(self)
        self.trade_event = Event()
        self.new_side = None
        self.BOTS_LIST = []

    def set_configurations(self, parameters):
        self.SYMBOL = parameters['symbol']
        self.TIME_FRAME = parameters['time_frame']
        self.BRICK_SIZE = float(parameters['brick_size'])
        self.ztl_resolution = float(parameters['ztl_resolution'])

        renko_config = {'brick_size': self.BRICK_SIZE,'ztl_res' : self.ztl_resolution}
        signal_config = {'symbol': self.SYMBOL, 'time_frame': self.TIME_FRAME}
        self.renko_calculator = Renko(renko_config)
        self.signaller = Signaller(self.renko_calculator, signal_config)
        self.renko_calculator.signaller = self.signaller  # needed for only get_historical_klines
        self.kline_feeder = BinanceKlines(self.SYMBOL, self.TIME_FRAME, [self.renko_calculator])

        self.signaller.trade_event_subscribers.append(self) #this class listens for trade events

        self.kline_feeder.start()
        self.renko_calculator.start()
        self.signaller.start()

    def run(self):
        '''
        lets listen for commands to create a new bot
        :return:
        '''
        print("running master")
        self.auto_trader()

    def auto_trader(self):
        while self.keep_running:
            logger.info("waiting for a trade event")
            self.trade_event.wait()
            logger.info("a trade event has been fired")
            if not self.new_side:
                logger.error(f"The side has not been set")
                self.trade_event.clear()
            if not self.BOTS_LIST:
                logger.error("no single bot registered")
            trade_params = {
                'side': self.new_side,
                'symbol': self.SYMBOL,
                'clients': self.BOTS_LIST
            }
            bm = Manager(trade_params)
            bm.start()
            bm.join()
            logger.info("trade has been completed successfully.")
            self.trade_event.clear()

    def create_new_bot(self, params):
        trade_params = {
            'side' : self.new_side,
            'symbol' : self.SYMBOL,
            'clients' : [params]
        }
        bm = Manager(trade_params)
        bm.start()
        bm.join()
        self.BOTS_LIST.append(params)

    def __del__(self):
        self.kline_feeder.keep_running = False
        self.renko_calculator.keep_running = False
        self.signaller.keep_running = False