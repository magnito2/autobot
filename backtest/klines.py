from binance.client import BinanceRESTAPI
import logging
from datetime import timedelta, datetime

logger = logging.getLogger("backtest.Klines")
UNITS = {"s":"seconds", "m":"minutes", "h":"hours", "d":"days", "w":"weeks", "M":"months"}

class Klines:

    def __init__(self, config):
        self.rest_api = BinanceRESTAPI()
        self.symbol = config['symbol']
        self.time_frame = config['time_frame']

    def get_historical_klines(self, startTime=None, endTime=None, limit=None):
        hist_klines = []
        while len(hist_klines) < limit:
            last_klines = self.rest_api.klines(symbol=self.symbol, interval=self.time_frame, startTime=startTime, endTime=endTime, limit=limit)
            hist_klines = last_klines + hist_klines
            endTime = hist_klines[0].open_time
            logger.debug(f"[+] fetching upto {datetime.fromtimestamp(int(endTime)/1000)}")
        return hist_klines

    def time_in_seconds(self, time_string):
        count = int(time_string[:-1])
        unit = UNITS[time_string[-1]]
        if unit == "months":
            unit = "weeks"
            count = count * 4
        td = timedelta(**{unit: count})
        return int(td.total_seconds())

    def get_limit_count(self, time_string, time_frame):
        seconds = self.time_in_seconds(time_string)
        interval = self.time_in_seconds(time_frame)
        count = int(seconds/interval)
        return count