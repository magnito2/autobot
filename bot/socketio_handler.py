'''
 since we are planning on using our socketio class to send messages through this handler, we will just pass
 the class.
'''

import json
import logging

class SocketIOHandler(logging.Handler):

    def __init__(self, websocket_manager):

        #initialize handler
        logging.Handler.__init__(self)
        self.ws = websocket_manager

    def emit(self, record):
        if self.ws:
            self.ws.emit('log', LogRecordEncoder().encode(record))


class LogRecordEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj.__dict__['record']
        except:
            return obj.__dict__