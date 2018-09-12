import threading

import logging
logger = logging.getLogger("abc.renko")

class Renko(threading.Thread):

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.up_trend = None
        self.down_trend = None
        self.signaller = None #signaller class needs to define method get_historical_klines
        self.brick_size = float(config['brick_size'])
        self.bricks = []
        self.klines = []
        self.kline_event = threading.Event()
        self.keep_running = True
        self.ready = threading.Event() #signaller should only start trading if this is true
        self.name = "RenkoCalc"
        self.ztl_res = float(config['ztl_res'])

    def run(self):
        '''
        main loop, checks for new klines and calls update renko
        :return: None
        '''

        historical_klines = self.signaller.get_historical_klines(limit=10000)
        if historical_klines:
            for kline in historical_klines:
                self.create_renko_bricks(kline, historical=True)
        self.trend = None
        if self.up_trend:
            self.trend = "[Up]"
            self.price_just_rose = True
        if self.down_trend:
            self.trend = "[Down]"
            self.price_just_dropped = True
        if self.up_trend and self.down_trend:
            self.trend = "[Confusion]"

        if self.up_trend or self.down_trend:
            logger.debug("Establishing initial conditions")
        else:
            logger.error("Unable to establish trend!, is your brick size too big?")

        logger.info("[+] Current trend is {} and I've just fetched {} bricks ;)".format(self.trend, len(self.bricks)))
        self.ready.set()
        while self.keep_running:
            try:
                self.kline_event.wait()
                if self.klines:
                    kline = self.klines.pop(0)
                    self.latest_price = float(kline.close)
                    self.create_renko_bricks(kline)
                else:
                    self.kline_event.clear()
            except Exception as e:
                logger.error(e)


    def create_renko_bricks(self, kline, historical = False):

        current_price = float(kline.close)

        if not historical:
            close_time = kline.end_time
            if not kline.is_final:
                return
            else:
                logger.debug("[+] Final Brick Price: {}".format(current_price))
        else:
            close_time = kline.close_time

        if len(self.bricks) == 0:
            close = current_price - (current_price % self.brick_size) #round off to the last brick size
            brick = Brick(0, close, close_time)
            self.bricks.append(brick)

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

            if current_price - last_brick.price >= self.brick_size * up_trend_factor:
                while current_price - last_brick.price >= self.brick_size * up_trend_factor:
                    next_brick_price = last_brick.price + self.brick_size * up_trend_factor
                    brick = Brick(last_brick.index + 1, next_brick_price, close_time)
                    self.bricks.append(brick)
                    last_brick = self.bricks[-1]
                    if not historical: #this helps in loading historic renkos silently.
                        logger.info("[Up] price up. new brick at: {}".format(last_brick))
                        if not self.up_trend:
                            self.trend = "UP"
                            up_trend_factor = 1 #this factor should only be 2 for the reversal brick, all other bricks 1
                        else:
                            logger.info("Price continuing to rise up")
                        self.signaller.renko_event.set()
                    self.up_trend = True
                    self.down_trend = False

                    self.get_last_ztl()  # a quick fix, shouldn't be done here, but

            elif last_brick.price - current_price >= self.brick_size * down_trend_factor:
                while last_brick.price - current_price >= self.brick_size * down_trend_factor:
                    next_brick_price = last_brick.price - self.brick_size * down_trend_factor
                    brick = Brick(last_brick.index + 1, next_brick_price, close_time)
                    self.bricks.append(brick)
                    last_brick = self.bricks[-1]
                    if not historical: #data is not historical
                        logger.info("[Down] Price down. new brick at: {}".format(last_brick))
                        if not self.down_trend:
                            self.trend = "DOWN"
                            down_trend_factor = 1 #this factor should be 2 only for the reversal brick, all other bricks 1
                        else:
                            logger.info("Price continuing to drop down")
                        self.signaller.renko_event.set()
                    self.down_trend = True
                    self.up_trend = False

                    self.get_last_ztl()  # quick fix, remove during optimization

            if len(self.bricks) > 500:
                self.bricks = self.bricks[-500:] #to avoid very long array, lets keep the last 500 values only

    def get_last_ztl(self):
        if not len(self.bricks):
            return 0
        brick = self.bricks[-1]
        if len(self.bricks) == 1: #the very first ztl will be the price fo first brick
            brick.ztl = brick.price
        else:
            if not hasattr(self.bricks[-2], "ztl"):
                self.bricks[-2].ztl = self.bricks[-2].price

            ztl_brick_size = self.bricks[-2].price * self.ztl_res
            if brick.price > self.bricks[-2].ztl + ztl_brick_size:
                brick.ztl = self.bricks[-2].ztl + ztl_brick_size
            elif brick.price < self.bricks[-2].ztl - ztl_brick_size:
                brick.ztl = self.bricks[-2].ztl - ztl_brick_size
            else:
                brick.ztl = self.bricks[-2].ztl
        return brick.ztl

    def __del__(self):
        print("[!] Main exiting")


class Brick:

    def __init__(self,index, price, close_time):
        self.index = index
        self.price = price
        self.close_time = close_time

    def __repr__(self):
        return f"<Brick{self.index} {self.close_time}: {self.price} indicator {self.ztl if hasattr(self, 'ztl') else self.sma if hasattr(self, 'sma') else 'none'}>"
