from bot import websocket_manager
import logging
import logging.handlers
from pytz import utc
import time

from bot.socketio_handler import SocketIOHandler

logger = logging.getLogger("renko")
logger.setLevel(logging.DEBUG)

logging.handlers.SocketIOHandler = SocketIOHandler
socketio_handler = SocketIOHandler(None)
logger.addHandler(socketio_handler)

fh = logging.handlers.RotatingFileHandler("logs/bot.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logging.Formatter.converter = time.localtime

websocket_manager.manage(socketio_handler)