'''
simple job, just know when conditions are right and shout "buy" or "sell"
'''

import threading
import logging
from .client_node import ClientNode

logger = logging.getLogger("abc.Manager")


class Manager(threading.Thread):

    def __init__(self, params):
        threading.Thread.__init__(self)
        self.keep_running = True
        self.symbol = params['symbol']
        self.name = "Manager"
        self.manual_trade_side = params['side']
        self.bots_params = params['clients']

    def run(self):
        '''
        this function now has to populate both renko_calculator and SMA_calculator
        :return:
        '''

        logger.debug("Waiting for renko calculator to be ready")

        self.manual_trade()


    def __del__(self):
        logger.error(f"[!] {self.name} is exiting")

    def manual_trade(self):

        if self.manual_trade_side in ['BUY', 'SELL'] and self.bots_params:
            self.create_clients(self.bots_params, self.manual_trade_side)

    def create_clients(self, client_list, side):

        clients = []
        for client in client_list:
            params = {
                'API_KEY' : client['API_KEY'],
                'API_SECRET' : client['API_SECRET'],
                'symbol' : self.symbol,
                'side' :  side,
                'name' : client['name'],
                'uuid' : client['uuid']
            }

            client_node = ClientNode(params)
            client_node.start()
            clients.append(client_node)

        for client_node in clients:
            client_node.join()
