from dashboard.app import new_user_registered, new_payment_made
from .email import send_email
from dashboard.app.models import User, Role
from flask import url_for, render_template

@new_user_registered.connect
def send_admin_notification(*args, **kwargs):
    print("[+] Event sending new user registered to Admins")
    user_id = kwargs['user_id']
    user = User.query.get(user_id)
    admin_role = Role.query.filter_by(name='Admin').first()
    admins_emails = [u.email for u in User.query.all() if admin_role in u.roles]
    print(f"{user} and {admins_emails}")
    if user and admins_emails:
        print(f"[+] User is {user.username}, admins are {admins_emails}")
        user_url = url_for('user', username=user.username, _external=True)
        html = render_template('email/new_user_registered.html', user_url=user_url, user=user)
        subject = "NEW REGISTRATION"
        send_email(admins_emails, subject, html)
    else:
        print("oops, a problem has occured")