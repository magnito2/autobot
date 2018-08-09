from flask_wtf import FlaskForm, Form, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from dashboard.app.models import User, Bot
import requests, time, hmac
from hashlib import sha256

class SearchForm(FlaskForm):
    search_value = StringField(DataRequired)
    submit = SubmitField()