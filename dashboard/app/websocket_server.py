'''
flask-socketio socket server
'''

from dashboard.app import app, db, activation_type
from dashboard.app import socketio
from flask_socketio import emit
import configparser
from dashboard.app.models import Bot
from dashboard.app.authorizer import activation_type

from dashboard.app import config_changed, new_bot_created, get_bot_status,  destroy_bot

@socketio.on('connect')
def test_connect():
    print("new connection")
    emit('message', {'data' : 'connected'})

def get_config():
    print('sending configurations')


@socketio.on('ready')
def make_res():
    print("responding to first message")
    send_config()

@socketio.on('botcreated')
def bot_created():
    print("recieved confirmation that new bot was created")
    emit('message',{'data' : "record saved"})

@socketio.on('getbots')
def get_bots():
    print("recieved request for new bots")
    bots = Bot.query.all()
    for bot in bots:
        if not activation_type(bot.id) == "expired":
            params = {
                'name': bot.name,
                'API_KEY': bot.api_key,
                'API_SECRET': bot.api_secret,
                'uuid' : bot.uuid
            }
            emit('create_new_bot', {'params' : params})
            socketio.sleep(0)

@socketio.on('getconfig')
def send_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    emit("global_config",
         {
             "params": {
                 "symbol": config['default']['symbol'],
                 "brick_size": config['default']['brick_size'],
                 "time_frame": config['default']['time_frame'],
                 "sma": config['default']['sma']
             }
         })

@config_changed.connect
def resend_config(app, **kwargs):
    config = configparser.ConfigParser()
    config.read("config.ini")
    socketio.emit("global_config",
         {
             "params": {
                 "symbol": config['default']['symbol'],
                 "brick_size": config['default']['brick_size'],
                 "time_frame": config['default']['time_frame'],
                 "sma": config['default']['sma']
             }
         })

@new_bot_created.connect
def send_new_bot(app, **kwargs):
    bot_id = kwargs['bot_id']
    bot = Bot.query.get(bot_id)
    if bot:
        params = {
            'name': bot.name,
            'API_KEY': bot.api_key,
            'API_SECRET': bot.api_secret,
            'uuid' : bot.uuid
        }
        socketio.emit('create_new_bot', {'params': params})

@destroy_bot.connect
def stop_bot(app, **kwargs):
    bot_id = kwargs['bot_id']
    bot = Bot.query.get(bot_id)
    if bot:
        params = {
            'uuid' : bot.uuid
        }
        socketio.emit('stop_bot', params)

@socketio.on('bots')
def bots_statuses(bots):
    print(bots)

@socketio.on('botstatus')
def bot_status(bot):
    print(f"[+] Recieved status for bot {bot}")
    if bot['bot']['uuid'] == None:
        print("The bot is not created yet")

@get_bot_status.connect
def ask_bot_status(app, **kwargs):
    if 'bot_id' in kwargs:
        bot_id = kwargs['bot_id']
        bot = Bot.query.get(bot_id)
        if bot:
            uuid = bot.uuid
            name = bot.name
            params = {
                'uuid' : uuid,
                'name' : name
            }
            socketio.emit('get_bot_status', params)
            return
    emit('get_bots_statuses')