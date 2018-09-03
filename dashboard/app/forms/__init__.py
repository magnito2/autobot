from flask_wtf import FlaskForm, Form, RecaptchaField
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import requests, time, hmac
from hashlib import sha256

from .search import SearchForm
from .new_email import NewEmailForm
from .users import LoginForm, RegistrationForm,EditProfileForm
from .bot import CreateBotForm
from .settings import SettingsForm
from .coinspayment import PaymentForm,CoinsPaymentForm

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

class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    message = TextAreaField(validators=[DataRequired()])
    submit = SubmitField('Create a new annoucement')