from flask_wtf import FlaskForm, Form, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from dashboard.app.models import User, Bot
import requests, time, hmac
from hashlib import sha256

from .search import SearchForm

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

def get_symbols():
    base_url = "https://api.binance.com"
    end_point = "/api/v1/exchangeInfo"
    try:
        resp = requests.get(base_url + end_point)
        data = resp.json()
        symbols = [sym['symbol'] for sym in data['symbols']]
        return symbols
    except:
        return ['BTCUSDT']

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

class SettingsForm(FlaskForm):
    symbol = SelectField('Symbol', validators=[DataRequired()], choices=[(sym, sym) for sym in get_symbols()])
    brick_size = IntegerField(
        'Brick Size', validators=[DataRequired()])

    time_frames = [
        ('1m', '1 minute'), ('3m', '3 minute'), ('5m', '5 minute'), ('15m', '15 minute'), ('30m', '30 minute'),
        ('1h', '1 hour'),
        ('2h', '2 hour'), ('4h', '4 hour'), ('6h', '6 hour'), ('8h', '8 hour'), ('12h', '12 hour'), ('1d', '1 day'),
        ('3d', '3 day'),
        ('1w', '1 week'), ('1M', '1 month')]
    time_frame = SelectField('Time Frame', validators=[DataRequired()], choices=time_frames)
    sma = IntegerField('SMA', validators=[DataRequired()])
    submit = SubmitField('Change Settings')

    def validate_symbol(self, symbol):
        symbols = get_symbols()
        if symbol.data not in symbols:
            raise ValidationError(f'The provided symbol is not in binance {symbol.data} {symbols}')

class PaymentForm(FlaskForm):
    currency = SelectField('Currency', validators=[DataRequired()], choices=[('BTC','BTC')])
    submit = SubmitField('Generate Payment Address')

class CoinsPaymentForm(FlaskForm):
    #ipn_version = IntegerField('ipn_version', validators=[DataRequired()])
    #ipn_type = StringField('ipn_type', validators=[DataRequired()])
    #ipn_mode = StringField('ipn_mode')
    ipn_id = StringField('ipn_id', validators=[DataRequired()])
    merchant = StringField('merchant', validators=[DataRequired()])

    address = StringField('address', validators=[DataRequired()])
    txn_id = StringField('txn_id', validators=[DataRequired()])
    status = IntegerField('status', validators=[DataRequired()])
    status_text = StringField('status_text', validators=[DataRequired()])
    currency = StringField('currency', validators=[DataRequired()])
    confirms = IntegerField('confirms', validators=[DataRequired()])
    amount = StringField('amount', validators=[DataRequired(), ])
    fee = StringField('fee')

class FeedbackForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    email = StringField(validators=[DataRequired(), Email()])
    subject = StringField()
    message = TextAreaField(validators=[DataRequired()])

class EmailForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=6, max=40)])
    submit = SubmitField('Submit')

class PasswordForm(Form):
    username = StringField('Username')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Reset Your Password')