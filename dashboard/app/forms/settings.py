from flask_wtf import FlaskForm
from wtforms import SubmitField, FloatField, SelectField
from wtforms.validators import ValidationError, DataRequired
import requests

def get_symbols():
    base_url = "https://api.binance.com"
    end_point = "/api/v1/exchangeInfo"
    try:
        resp = requests.get(base_url + end_point)
        data = resp.json()
        symbols = [sym['symbol'] for sym in data['symbols'] if "BTC" in sym['symbol']]
        return symbols
    except:
        return ['BTCUSDT']

class SettingsForm(FlaskForm):
    symbol = SelectField('Symbol', validators=[DataRequired()], choices=[(sym, sym) for sym in get_symbols()])
    brick_size = FloatField(
        'Brick Size', validators=[DataRequired()])

    time_frames = [
        ('1m', '1 minute'), ('3m', '3 minute'), ('5m', '5 minute'), ('15m', '15 minute'), ('30m', '30 minute'),
        ('1h', '1 hour'),
        ('2h', '2 hour'), ('4h', '4 hour'), ('6h', '6 hour'), ('8h', '8 hour'), ('12h', '12 hour'), ('1d', '1 day'),
        ('3d', '3 day'),
        ('1w', '1 week'), ('1M', '1 month')]
    time_frame = SelectField('Time Frame', validators=[DataRequired()], choices=time_frames)
    #sma = IntegerField('SMA', validators=[DataRequired()])
    ztl_resolution = FloatField("ZTL Resolution", validators=[DataRequired()])
    submit = SubmitField('Change Settings')

    def validate_symbol(self, symbol):
        symbols = get_symbols()
        if symbol.data not in symbols:
            raise ValidationError(f'{symbol.data} is not a symbol in binance')
