from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests, time, hmac
from hashlib import sha256

class CreateBotForm(FlaskForm):
    api_key = StringField('Api Key', validators=[DataRequired()])
    api_secret = StringField('Api Secret', validators=[DataRequired()])
    submit = SubmitField('Create/Edit Bot')

    def __init__(self, current_user, *args, **kwargs):
        super(CreateBotForm, self).__init__(*args, **kwargs)
        self.current_user = current_user

    def validate(self):
        if not Form.validate(self):
            return False

        return True

    def validate_api_key(self, api_key):
        full_url = 'https://api.binance.com/api/v3/account'
        payload = {'timestamp': int(time.time() * 1000)}
        signature_parameter_string = "&".join(["%s=%s" % (key, value) for key, value in payload.items()])
        sig = hmac.new(self.api_secret.data.encode(), signature_parameter_string.encode(), sha256).hexdigest()

        payload['signature'] = sig

        headers = {'X-MBX-APIKEY': self.api_key.data}

        response = requests.get(full_url, headers=headers, params=payload)

        if not response.status_code == 200:
            print(response.text)
            message = response.json()['msg']
            self.api_key.errors.append(message)
            return False