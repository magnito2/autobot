'''
flask-socketio socket server
'''

from dashboard.app import app, db, activation_type
from dashboard.app import socketio
from flask_socketio import emit, send
import configparser
from dashboard.app.models import Bot, Log
from dashboard.app.authorizer import activation_type

from dashboard.app.signals import config_changed, new_bot_created, get_bot_status,  destroy_bot, confirm_change_config, confirmed_do_change_settings, bot_error_log

import json, datetime

@socketio.on('connect')
def test_connect():
    print("new connection")
    emit('message', {'data' : 'connected'})

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
        if not activation_type(bot.id) == "expired" and bot.can_trade:
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
    config.read(app.config['CONFIG_INI_FILE'])
    emit("global_config",
         {
             "params": {
                 "symbol": config['default']['symbol'],
                 "brick_size": config['default']['brick_size'],
                 "time_frame": config['default']['time_frame'],
                 #"sma": config['default']['sma'],
                 "ztl_resolution" : config['default']['ztl_resolution'],
                 #"indicator" : config['default']['indicator']
             }
         })

@socketio.on('log')
def log_this(log):
    log_dict = json.loads(log)
    log = Log(
        name = log_dict['name'],
        msg = log_dict['msg'],
        levelname= log_dict['levelname'],
        threadName= log_dict['threadName'],
        #created= datetime.datetime.fromtimestamp(log_dict['created'])
    )
    db.session.add(log)
    db.session.commit()
    if log.levelname == "ERROR":
        print("bot has raised an error")
        bot_error_log.send(log_dict)

@config_changed.connect
def resend_config(app2, **kwargs):
    print("We are heree!!")
    config = configparser.ConfigParser()
    config.read(app.config['CONFIG_INI_FILE'])
    socketio.emit("global_config",
         {
             "params": {
                 "symbol": config['default']['symbol'],
                 "brick_size": config['default']['brick_size'],
                 "time_frame": config['default']['time_frame'],
                 #"sma": config['default']['sma'],
                 'ztl_resolution' : config['default']['ztl_resolution']
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
    socketio.emit('bots_status', bots)

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

@confirm_change_config.connect
def confirm_pair_change(*args, **kwargs):
    print("emiting confirm pair change")
    params = kwargs["params"]
    socketio.emit("confirmpairchange", params)

@socketio.on('dochangepair')
def do_change_pair(params, **kwargs):
    socketio.emit("bot_do_change_pair", params)
    confirmed_do_change_settings.send(params)