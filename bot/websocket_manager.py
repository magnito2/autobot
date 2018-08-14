from socketIO_client import SocketIO, BaseNamespace
from bot.master import Master
import os,sys

import logging
import logging.handlers

logger = logging.getLogger("renko.ws_manager")

class MasterNamespace(BaseNamespace):

    def on_connect(self):
        logger.info('[Connected]')

    def on_create_new_bot(self, *args):
        logger.info("[*] creating a new bot")
        data = args[0]
        params = data['params']
        logger.debug(f'[*] Params passed: {params}')
        self.master.create_new_bot(params)
        self.emit('botcreated')

    def on_global_config(self,  *args):
        logger.info("[*] Changing the master configurations")
        data = args[0]
        params = data['params']
        logger.debug(f"[*] Params passed: {params}")
        self.master.set_configurations(params)
        self.emit('configschanged')

    def on_config_change(self, *args):
        logger.info("[*] Server changed the config, restarting bots")
        os.execv(sys.executable, ['python'] + sys.argv)

    def on_message(self, data):
        pass

    def on_get_bots_statuses(self, *args):
        logger.info("[*] Getting status of the bots")
        bots = []
        for bot in self.master.BOTS_LIST:
            params = {
                'uuid' : bot.uuid,
                'is_alive' : bot.is_alive()
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
            if bot.uuid == uuid:
                bot_list.append(bot)
                break
        if bot_list:
            bot = bot_list[0]
            params = {
                'uuid': bot.uuid,
                'is_alive': bot.is_alive()
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


def on_connect():
    print("*"*100)
    print("[+] Connected")
def disconnected():
    print("*" * 100)
    print("[+] Disconnected")
def reconnect():
    print("*" * 100)
    print("[+] Reconnected")

def manage(socketio_handler):
    socketIO = SocketIO('https://autobotcloud.com', Namespace= MasterNamespace)
    namespace = socketIO.get_namespace()
    socketIO.on('connect', on_connect)
    socketIO.on('disconnect', disconnected)
    namespace.master = Master()
    socketio_handler.ws = socketIO #trial code to hand over this instance of socketio to logging
    socketIO.emit('ready')
    logger.info("emitted ready")
    socketIO.emit('getbots')
    logger.info("emitted get bots")
    socketIO.wait()