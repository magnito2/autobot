from socketIO_client import SocketIO, BaseNamespace
from bot.master import Master
import time

import logging
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
        self.master.restart()

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
        for bot in self.master.BOTS_LIST:
            if bot.uuid == uuid:
                params = {
                    'uuid' : bot.uuid,
                    'is_alive' : bot.is_alive()
                }
                break
        logger.info(f"[+] Informing on bot {uuid}")
        self.emit('botstatus',{'bot' : params})

    def on_stop_bot(self, *args):
        uuid = args[0]['uuid']
        params = None
        for bot in self.master.BOTS_LIST:
            if bot.uuid == uuid:
                bot.keep_running = False
                params = {
                    'uuid' : bot.uuid,
                    'is_alive' : bot.is_alive()
                }
                break
        logger.info(f"[+] Informing on stopping bot {uuid}")
        self.emit('botstatus',{'bot' : params})




def manage():
    socketIO = SocketIO('localhost', 5000, MasterNamespace)
    namespace = socketIO.get_namespace()
    namespace.master = Master()
    socketIO.emit('ready')
    logger.info("emitted ready")
    socketIO.emit('getbots')
    logger.info("emitted get bots")
    socketIO.wait()


