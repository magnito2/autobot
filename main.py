from bot import websocket_manager
import logging
import logging.handlers

logger = logging.getLogger("renko")
logger.setLevel(logging.DEBUG)

fh = logging.handlers.RotatingFileHandler("logs/bot.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)



websocket_manager.manage()