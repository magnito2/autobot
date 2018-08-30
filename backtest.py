'''
backtest entry point
'''
from backtest.trader import Trader
import logging
import logging.handlers
import configparser


logger = logging.getLogger("backtest")
logger.setLevel(logging.DEBUG)

fh = logging.handlers.RotatingFileHandler("logs/backtest.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


parser =configparser.ConfigParser()
parser.read('backtest/backtest.ini')
config = {
    'symbol' : parser['default']['SYMBOL'],
    'time_frame' : parser['default']['TIME_FRAME'],
    'brick_size' : parser['default']['BRICK_SIZE'],
    'SMA' : int(parser['default']['SMA']),
    'limit' : parser['default']['LIMIT'],
    'indicator' : parser['default']['indicator'],
    'ztl_res' : parser['default']['ztl_res']
}
trader = Trader(config)
trader.run()