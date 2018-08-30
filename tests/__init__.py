'''
testing, will grow to unit testing later on
'''

from bot.signaller import Signaller
from bot.new_klines_feeder import BinanceKlines
from bot.new_renko import Renko

configs = {
    'symbol' : 'BTCUSDT',
    'time_frame' : '1m',
    'brick_size' : 20,
    'SMA' : 10
}

def test():
    renko = Renko(configs)
    bk = BinanceKlines(configs['symbol'], configs['time_frame'], [renko])
    signaller = Signaller(renko, configs)
    renko.signaller = signaller

    bk.start()
    renko.start()
    signaller.start()