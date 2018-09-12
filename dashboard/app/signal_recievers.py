from dashboard.app.signals import new_user_registered, confirmed_do_change_settings,  bot_error_log, trade_manually
from .email import send_email
from dashboard.app.models import User, Role, Bot
from flask import url_for, render_template
import configparser
from dashboard.app import app,socketio
from dashboard.app.authorizer import activation_type

@new_user_registered.connect
def send_admin_notification(*args, **kwargs):
    print("[+] Event sending new user registered to Admins")
    user_id = kwargs['user_id']
    user = User.query.get(user_id)
    admin_role = Role.query.filter_by(name='Admin').first()
    admins_emails = [u.email for u in User.query.all() if admin_role in u.roles]
    print(f"{user} and {admins_emails}")
    if user and admins_emails:
        print(f"[+] User is {user.username}, admins are {admins_emails}")
        user_url = url_for('users.user', username=user.username, _external=True)
        html = render_template('email/new_user_registered.html', user_url=user_url, user=user)
        subject = "NEW REGISTRATION"
        send_email(admins_emails, subject, html)
    else:
        print("oops, a problem has occured")

@confirmed_do_change_settings.connect
def do_change_settings(*args, **kwargs):
    params = args[0]
    print(f"We are at confirmed with {params}")
    config = configparser.ConfigParser()
    config['default'] = {
        'symbol': params['symbol'],
        'time_frame': params['time_frame'],
        'brick_size': params['brick_size'],
        #'sma': params['sma'],
        'ztl_resolution' : params['ztl_resolution']
    }
    with open(app.config['CONFIG_INI_FILE'], 'w') as configfile:
       config.write(configfile)

@bot_error_log.connect
def handle_bot_error(*args):
    log_dict = args[0]
    print(f"We have recieved an error!!!! {log_dict}")
    socketio.emit("bot-error", log_dict)

@trade_manually.connect
def manual_trade(side):
    print(f"recieved a signal to {side} manually")
    config = configparser.ConfigParser()
    config.read(app.config['CONFIG_INI_FILE'])

    if not side in ['BUY', 'SELL']:
        print(f"Side not understood, use BUY or SELL, side : {side}")
        return
    bots = Bot.query.all()
    bot_list = []
    for bot in bots:
        if not activation_type(bot.id) == "expired" and bot.can_trade:
            bot_params = {
                'API_KEY' : bot.api_key,
                'API_SECRET' : bot.api_secret,
                'name' : bot.name,
                'uuid' : bot.uuid
            }
            bot_list.append(bot_params)
    symbol = config['default']['symbol']
    params = {'clients' : bot_list, 'side' : side,  'symbol' : symbol}
    socketio.emit('manual_trade', params)