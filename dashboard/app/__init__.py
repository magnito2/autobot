from flask import Flask
from dashboard.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flaskext.markdown import Markdown
from flask_pagedown import PageDown
from blinker import Namespace
from flask_cors import CORS, cross_origin

from dashboard.app.momentjs import momentjs

app = Flask(__name__, static_url_path="")
#app.debug = True
app.config.from_object(Config)
app.static_folder = app.config['STATIC_FOLDER']
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'account.login'
socketio = SocketIO(app)
mail = Mail(app)
CSRFProtect(app)
Markdown(app)
PageDown(app)
CORS(app)

app_signals = Namespace()

app.jinja_env.globals['momentjs'] = momentjs

from dashboard.app.authorizer import authorize, activation_type, trial_days_remaining, active_days_remaining, get_remaining_subscription_days
from dashboard.app.decorators import gravitate
app.jinja_env.globals['authorize'] = authorize
app.jinja_env.globals['activation_type'] = activation_type
app.jinja_env.globals['trial_days_remaining'] = trial_days_remaining
app.jinja_env.globals['active_days_remaining'] = active_days_remaining
app.jinja_env.globals['get_remaining_subscription_days'] = get_remaining_subscription_days
app.jinja_env.globals['gravitate'] = gravitate

#flask style import everything
from dashboard.app import models, errors, websocket_server, signal_recievers, routes, app_socketio, signals

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)