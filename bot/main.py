from new_renko import Renko
from signaller import Signaller
from new_orders import Orders
from klines_feeder import BinanceKlines
import configparser
from colorama import init, Fore
from custom_client import CustomClient
from settings import *
import time

import logging

logger = logging.getLogger("shell_renko")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("test.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

import logo


def main():
    init(autoreset=True)
    config = configparser.ConfigParser()
    config.read('config.ini')
    time_frame = config['DEFAULT']['time_frame']
    symbol = config['DEFAULT']['symbol']
    brick_size = float(config['DEFAULT']['brick_size'])
    no_items_2_avg = float(config['DEFAULT']['SMA'])
    if time_frame not in time_frames_intervals:
        raise ValueError(Fore.RED + "time frame needs to be one of {}".format(time_frames_intervals))

    logger.info("Configs:: Symbol: {}, Interval: {}, Brick Size: {}".format(symbol, time_frame, brick_size))

    renko_config = {'brick_size': brick_size, 'SMA' : no_items_2_avg}
    signal_config = {'symbol': symbol, 'time_frame': time_frame}
    renko_calculator = Renko(renko_config)
    signaller = Signaller(renko_calculator, signal_config)
    renko_calculator.signaller = signaller #needed for only get_historical_klines

    klines_feeder = BinanceKlines(symbol, time_frame, [renko_calculator])
    klines_feeder.setDaemon(True)
    klines_feeder.start()

    order_params = {'API_KEY': API_KEY, 'API_SECRET': API_SECRET, 'symbol': symbol}
    order_class = Orders(signaller, order_params)
    order_class.start()

    signaller.trade_event_subscribers.append(order_class)

    renko_calculator.start()
    signaller.start()


if __name__ == "__main__":
    main()
