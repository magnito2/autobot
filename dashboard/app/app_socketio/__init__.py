'''
will contain websocket communication to both the bot and clients
'''

from dashboard.app import socketio, app
from dashboard.app.models import Log
from sqlalchemy import desc
from flask_socketio import emit, send
from dashboard.app.decorators import my_get_paginated_list

@socketio.on('message')
def handle_my_message(*args):
    print(f'received message: {args}')

@socketio.on('configschanged')
def done_changing_configs():
    print("bot has changed configurations")
    socketio.emit("done_changing_configs")

@socketio.on("get-logs")
def send_logs(*args, **kwargs):
    print(f"our args are {args}")
    print(f"our kwargs are {kwargs}")
    page = args[0] if args else 1
    search_word = None
    if len(args) > 1:
        search_word = args[1]['search_value']
    if search_word:
        print("*" * 100)
        print(f"we have a search word!! {search_word}")

    paginated_logs = my_get_paginated_list(Log, page, search_word)

    emit("bot-log", paginated_logs)

@socketio.on("search-logs")
def send_searched_logs(*args):
    search_term = args[0]
    page = args[1] if args[1] else 1
