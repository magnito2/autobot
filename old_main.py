from renko import Renko
import argparse, configparser, time
from settings import *
import logging
import logging.handlers
from colorama import init, Fore
from dashboard.websocket_server import KlinesServer
from dashboard.logging_socket_handler import WebSocketFormatter, SocketHandler

import logo

from klines import BinanceKlines
from orders import Orders

import asyncio

logger = logging.getLogger("RenkoBot")
logger.setLevel(logging.DEBUG)

fh = logging.handlers.RotatingFileHandler("bot.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)



class Config:

    def __init__(self, silent):
        self.silence = silent
        self.load_config()
        self.first_trade = False

    def load_config(self):
        '''
        loads config.ini
        :return:
        '''
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.time_frame = config['DEFAULT']['time_frame']
        self.symbol = config['DEFAULT']['symbol']
        self.brick_size = float(config['DEFAULT']['brick_size'])
        self.quantity = float(config['DEFAULT']['quantity'])
        if self.time_frame not in time_frames_intervals:
            raise ValueError(Fore.RED + "time frame needs to be one of {}".format(time_frames_intervals))

        if not self.silence:
            print(Fore.BLUE + "----------------CONFIGURATIONS----------------")
            print(Fore.CYAN + "Symbol: {}, Interval: {}, Brick Size: {}".format(self.symbol, self.time_frame, self.brick_size))
            print("------------------------------------------")
            logger.info("\n\n")
            logger.info("--------STARTING BOT------------")
            logger.info("Configs:: Symbol: {}, Interval: {}, Brick Size: {}".format(self.symbol, self.time_frame, self.brick_size))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", type=bool, help="make the bot restart silently, will not display restart logo and message",
                        )
    args = parser.parse_args()
    if args.silent:
        print("restarting bot")
        silent=True
    else:
        silent=False
        print("starting binance renko bot")
        logo.print_logo()

    config = Config(silent)

    renko_bot = Renko(logger, config, silent=silent)
    order_factory = Orders(config, renko_bot, logger)
    order_factory.start()

    loop = asyncio.new_event_loop()
    klines_socket = KlinesServer(loop, config)
    klines_socket.start()

    subscribers = [klines_socket, renko_bot]

    klines_feeder = BinanceKlines(config.symbol, config.time_frame, subscribers)
    klines_feeder.start()
    renko_bot.start()
    klines_socket.renko_bot = renko_bot

    print("now we wait for everyone to finish")


if __name__ == "__main__":
    main()