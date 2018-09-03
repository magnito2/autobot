from dashboard.app import db
from datetime import datetime
from hashlib import sha256
import uuid, hmac, requests, time


class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    uuid = db.Column(db.String(64), default=str(uuid.uuid4()))
    api_key = db.Column(db.String(140))
    api_secret = db.Column(db.String(140))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    can_trade = db.Column(db.Boolean, default=True)

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