from socketIO_client import SocketIO, BaseNamespace
from new_bot.master import Master
import os,sys
from new_bot.bot_manager import Manager

import logging
import logging.handlers

logger = logging.getLogger("abc.ws_manager")

class MasterNamespace(BaseNamespace):

    def on_connect(self):
        logger.info('[Connected]')

    def on_create_new_bot(self, *args):
        data = args[0]
        params = data['params']
        logger.debug(f'[*] Params passed: {params}')
        self.master.create_new_bot(params)
        self.emit('botcreated')

    def on_global_config(self,  *args):
        data = args[0]
        params = data['params']
        logger.debug(f"[*] Params passed: {params}")
        if not self.master.SYMBOL == params['symbol'] or not self.master.TIME_FRAME == params['time_frame'] \
                or not self.master.ztl_resolution == params['ztl_resolution'] or not self.master.BRICK_SIZE == params['brick_size']:
            logger.info("[*] Changing the master configurations")
            params['socketio_client'] = self
            self.master.set_configurations(params)
            self.emit('configschanged')

    def on_config_change(self, *args):
        logger.info("[*] Server changed the config, restarting bots")
        os.execv(sys.executable, ['python'] + sys.argv)

    def on_get_bots_statuses(self, *args):
        logger.info("[*] Getting status of the bots")
        bots = []
        for bot in self.master.signaller.trade_event_subscribers:
            params = {
                'uuid' : bot.uuid,
                'is_alive' : bot.is_alive(),
                'name' : bot.name
            }
            bots.append(bot)
        logger.debug(f"bots statuses {bots}")
        self.emit('bots', {'bots' : bots})

    def on_get_bot_status(self, *args):
        params = None
        uuid = args[0]['uuid']
        name = args[0]['name']
        bot_list = []
        for bot in self.master.BOTS_LIST:
            if bot['uuid'] == uuid:
                bot_list.append(bot)
                break
        if bot_list:
            bot = bot_list[0]
            params = {
                'uuid': bot['uuid']
            }
        else:
            params = {
                'uuid': None,
                'is_alive': False
            }

        logger.info(f"[+] Informing on bot {uuid}")
        self.emit('botstatus',{'bot' : params})

    def on_stop_bot(self, *args):
        print(f"[+] Recieved stop bot,{args}")
        uuid = args[0]['uuid']
        params = None
        for bot in self.master.BOTS_LIST:
            if bot.uuid == uuid:
                bot.keep_running = False
                bot.trade_event.set() #make it clear of
                params = {
                    'uuid' : bot.uuid,
                    'is_alive' : bot.is_alive()
                }
                break
        logger.info(f"[+] Informing on stopping bot {uuid}")
        self.emit('botstatus',{'bot' : params})

    def on_bot_do_change_pair(self, *args):
        '''
        This function will be called when the server's global configuration changes.
        1. Tell all bots to convert the currencies to BTC.
        2. When all bots complete their trades, ask for global config.
        :param args:
        :return:
        '''
        print(f"params passed are {args}")
        self.master.gracefully_end_all_trades()
        self.emit("ready")

    def on_request_renko_bricks(self, *args):
        '''
        when a client opens a chart, server sends this guy a request to send all current bricks
        :param args:
        :return:
        '''
        bricks = self.master.renko_calculator.bricks
        brick_list = []
        for index, brick in enumerate(bricks):
            prev_brick = bricks[index-1] if index > 0 else None
            if prev_brick:
                if brick.price > prev_brick.price:
                    high = brick.price
                    bull = True
                else:
                    high = brick.price + self.master.renko_calculator.brick_size
                    bull = False
            else:
                high = None
                bull = None

            brick_list.append({
                'price' : brick.price,
                'time' : brick.close_time,
                'index' : brick.index,
                'high' : high,
                'bull' : bull,
                'ztl' : brick.ztl
            })
        logger.info("responding to request for renko bricks")
        self.emit("renkobricks", brick_list)

    def on_manual_trade(self, kwargs):
        side = kwargs['side'] if 'side' in kwargs and kwargs['side'] in ['BUY', 'SELL'] else None
        clientelle = kwargs['clients'] if 'clients' in kwargs else []
        client_list = []
        for client in clientelle:
            params = {
                'API_KEY' : client['API_KEY'],
                'API_SECRET' : client['API_SECRET'],
                'name' : client['name'],
                'uuid' : client['uuid'],
                'symbol' : kwargs['symbol'],
                'side' : side
            }
            client_list.append(params)
        manager_params = {'clients' : client_list, 'symbol' : kwargs['symbol'], 'side' : side}
        print(f"[+] Sending the following to the manager {manager_params}")
        manual_manager = Manager(manager_params)
        manual_manager.start()

def connected():
    print("*"*100)
    print("[+] Connected")
def disconnected():
    print("*" * 100)
    print("[+] Disconnected")
def reconnect():
    print("*" * 100)
    print("[+] Reconnected")

def manage(socketio_handler):
    socketIO = SocketIO('http://localhost:5000', Namespace= MasterNamespace)
    #socketIO = SocketIO('https://autobotcloud.com', Namespace=MasterNamespace)
    namespace = socketIO.get_namespace()
    socketIO.on('connect', connected)
    socketIO.on('disconnect', disconnected)
    namespace.master = Master()
    namespace.master.start()

    socketio_handler.ws = socketIO #trial code to hand over this instance of socketio to logging
    socketIO.emit('ready')
    logger.info("emitted ready")
    socketIO.emit('getbots')
    logger.info("emitted get bots")
    socketIO.wait()