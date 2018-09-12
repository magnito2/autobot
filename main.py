from bot import websocket_manager
import logging
import logging.handlers
from pytz import utc
import time

from bot.socketio_handler import SocketIOHandler
logging.Formatter.converter = time.gmtime

class UTCFormatter(logging.Formatter):
    converter = time.gmtime

logger = logging.getLogger("renko")
logger.setLevel(logging.DEBUG)

logging.handlers.SocketIOHandler = SocketIOHandler
socketio_handler = SocketIOHandler(None)

utc_formatter = UTCFormatter()
socketio_handler.setFormatter(utc_formatter)

logger.addHandler(socketio_handler)


fh = logging.handlers.RotatingFileHandler("logs/bot.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
formatter.converter = time.gmtime
fh.setFormatter(formatter)
logger.addHandler(fh)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

websocket_manager.manage(socketio_handler)