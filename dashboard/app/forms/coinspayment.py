from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired


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
