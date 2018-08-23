# project/email.py

from flask_mail import Message
from flask import url_for, render_template
from dashboard.app import app, mail
from itsdangerous import URLSafeTimedSerializer
from .decorators import async

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template):
    if isinstance(to, str):
        to = [to]
    msg = Message(
        subject,
        recipients=to,
        html=template,
        sender=app.config['MAIL_USERNAME']
    )
    #mail.send(msg)
    send_async_email(app, msg)

def send_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'account.reset_with_token',
        token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template('email/email_password_reset.html',password_reset_url=password_reset_url)

    send_email([user_email], 'Password Reset Requested', html)