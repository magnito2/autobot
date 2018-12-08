from .models import Role, Bot
from functools import wraps
from flask import request, redirect, url_for, flash
from flask_login import current_user
import datetime
import hmac
from hashlib import sha512
from dashboard.app import app
from flask import abort

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            check_role = Role.query.filter_by(name=role).first()
            if check_role and current_user.is_authenticated:
                if not check_role in current_user.roles:
                    return redirect(url_for('home.index'))
                return f(*args, **kwargs)
            return redirect(url_for('account.login', next=request.url))
        return decorated_function
    return decorator

def authorize(role):
    check_role = Role.query.filter_by(name=role).first()
    if check_role and current_user.is_authenticated:
        return check_role in current_user.roles
    return False

def activation_type(bot_id = None):
    current_time = datetime.datetime.utcnow().timestamp()
    trial_duration = 30*24*60*60
    if not bot_id:
        return "create"
    bot = Bot.query.get(bot_id)
    if not bot:
        account_type = "unknown"
    elif bot.expires_at and bot.created_at:
        if current_time < bot.expires_at.timestamp():
            account_type = "active"
        elif current_time < bot.created_at.timestamp() + trial_duration:
            account_type = "trial"
        else:
            account_type = "expired"
    else:
        return "unknown"
    return account_type

def trial_days_remaining(bot_id):
    current_time = datetime.datetime.utcnow().timestamp()
    trial_duration = 30 * 24 * 60 * 60
    if not bot_id:
        return 0
    bot = Bot.query.get(bot_id)
    if not bot:
        return 0
    elif bot.expires_at and bot.created_at:
        if current_time < bot.created_at.timestamp() + trial_duration:
            return int((bot.created_at.timestamp() + trial_duration - current_time)/86400)
        else:
            return 0
    else:
        return 0

def active_days_remaining(bot_id):
    current_time = datetime.datetime.utcnow().timestamp()
    if not bot_id:
        return 0
    bot = Bot.query.get(bot_id)
    if not bot:
        return 0
    return int((bot.expires_at.timestamp() - current_time)/86400)

def get_remaining_subscription_days(bot_id):
    if activation_type(bot_id) == "trial":
        return trial_days_remaining(bot_id)
    elif activation_type(bot_id) == "active":
        return active_days_remaining(bot_id)
    elif activation_type(bot_id) == "expired":
        return activation_type(bot_id)

def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.active is False:
            #flash('Please confirm your account!', 'warning')
            return redirect(url_for('users.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

def check_hmac(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        data = request.get_data(as_text=True)
        sig = hmac.new(app.config['HMAC_KEY'].encode(), data.encode(), sha512).hexdigest()
        server_hmac = request.headers['HMAC']
        if not sig == server_hmac:
            abort(401)
        return func(*args, **kwargs)

    return decorated_function

def ws_check_hmac(func):
    data = request.get_data(as_text=True)
    sig = hmac.new(app.config['HMAC_KEY'].encode(), data.encode(), sha512).hexdigest()
    server_hmac = request.headers['HMAC']
    if not sig == server_hmac:
        abort(401)
    return True