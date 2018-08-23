from dashboard.app import app, db
from flask_login import current_user
from datetime import datetime

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix="/dashboard")
bots_bp = Blueprint('bots', __name__, url_prefix="/bots")
payment_bp = Blueprint('payments', __name__, url_prefix="/payments")
settings_bp = Blueprint('settings', __name__, url_prefix="/settings")
account_bp = Blueprint('account', __name__, url_prefix="/account")
user_bp = Blueprint('users', __name__, url_prefix="/users")
home_bp = Blueprint('home', __name__)
log_bp = Blueprint('logs', __name__, url_prefix="/logs")
stats_bp = Blueprint('stats', __name__, url_prefix="/stats")

from . import admin, bots, home, payments, settings, users, account, logs, stats

app.register_blueprint(admin_bp)
app.register_blueprint(bots_bp)
app.register_blueprint(home_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(user_bp)
app.register_blueprint(account_bp)
app.register_blueprint(log_bp)
app.register_blueprint(stats_bp)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()