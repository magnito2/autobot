from dashboard.app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from dashboard.app import login
from hashlib import md5, sha256
import uuid, hmac, requests, time

from .log import Log

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    bots = db.relationship('Bot', backref='owner', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_confirmed_at = db.Column(db.DateTime())

    # Relationships
    roles = db.relationship('Role', secondary='user_roles')
    payments = db.relationship('Payment', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    uuid = db.Column(db.String(64), default=str(uuid.uuid4()))
    api_key = db.Column(db.String(140))
    api_secret = db.Column(db.String(140))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def get_account_balance(self):
        full_url = 'https://api.binance.com/api/v3/account'
        payload = {'timestamp': int(time.time() * 1000)}
        signature_parameter_string = "&".join(["%s=%s" % (key, value) for key, value in payload.items()])
        sig = hmac.new(self.api_secret.encode(), signature_parameter_string.encode(), sha256).hexdigest()

        payload['signature'] = sig

        headers = {'X-MBX-APIKEY': self.api_key}

        try:
            response = requests.get(full_url, headers=headers, params=payload)

            if not response.status_code == 200:
                return []

            data = response.json()['balances']
            return [x for x in data if float(x['free']) > 0 and x['asset'] in ['BTC', 'USDT']]
        except Exception as e:
            return []

    def __repr__(self):
        return '<Bot {}>'.format(self.name)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role {}>'.format(self.name)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer(), primary_key=True)
    ipn_id = db.Column(db.String(64), unique=True)
    txn_id = db.Column(db.String(64), unique=True)
    status = db.Column(db.String(64))
    status_text = db.Column(db.String(128))
    currency1 = db.Column(db.String(32))
    currency2 = db.Column(db.String(32))
    amount1 = db.Column(db.Integer())
    amount2 = db.Column(db.Integer())
    fee = db.Column(db.String(50))
    buyer_name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    item_name = db.Column(db.String(64))
    item_number = db.Column(db.String(64))
    send_tx = db.Column(db.String(64))
    recieved_amount = db.Column(db.String(64))
    recieved_confirms = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_complete = db.Column('is_complete', db.Boolean(), nullable=False, server_default='0')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Payment {self.txn_id} {self.amount2} {self.currency2}>"

class Feedback(db.Model):
    __tablename__='feedbacks'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    subject = db.Column(db.Text())
    message = db.Column(db.Text())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.id} {self.subject} from {self.name}>"

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
