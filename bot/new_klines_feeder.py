from binance.client import Client
from binance.websockets import BinanceSocketManager
from threading import Thread, Event
import time, logging
from twisted.internet import reactor
from bot.models import KLineEvent

logger = logging.getLogger("renko.new_klines")

class BinanceKlines(Thread):

    def __init__(self, symbol, interval, subscribers):
        Thread.__init__(self)
        self.symbol = symbol
        self.interval = interval
        self.subscribers = subscribers
        self.rest_client = Client(None, None)
        self.ws_client = BinanceSocketManager(self.rest_client)
        self.restart_count = 1

    def run(self):
        conn_key = self.ws_client.start_kline_socket(self.symbol, self.on_message, self.interval)
        self.ws_client.start()
        self.ws_client.join()

    def on_message(self, msg):
        #to recieve notifications, subscibers should have an array called klines and an event called kline_event
        #kline = Kline(msg)
        kline = KLineEvent.object_from_dictionary(msg)
        for subscriber in self.subscribers:
            subscriber.klines.append(kline)
            subscriber.kline_event.set()

    def __del__(self):
        self.ws_client = None
        logger.info("Klines stopping")

    def close(self):
        self.keep_running = False
        self.ws_client.close()
        reactor.stop()

class Kline:
    def __init__(self, msg):
        self.raw_data = msg['k']
        self.start_time = self.raw_data['t']
        self.end_time = self.raw_data['T']
        self.symbol = self.raw_data['s']
        self.interval = self.raw_data['i']
        self.first_trade_id = self.raw_data['f']
        self.last_trade_id = self.raw_data['L']
        self.open = self.raw_data['o']
        self.close = self.raw_data['c']
        self.high = self.raw_data['h']
        self.low = self.raw_data['l']
        self.base_asset_volume = self.raw_data['v']
        self.number_of_trades = self.raw_data['n']
        self.is_this_kline_closed = self.raw_data['x']
        self.quote_asset_volume = self.raw_data['q']
        self.taker_buy_base_asset_volume = self.raw_data["V"]
        self.taker_buy_quote_asset_volume = self.raw_data["Q"]
        self.event_time = msg['E']

    def __repr__(self):
        return f"<Kline {self.symbol} {self.event_time}>"
