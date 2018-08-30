from dashboard.app.routes import account_bp
from flask_login import login_required, logout_user, login_user, current_user
from flask import redirect, url_for, render_template, request, flash
from dashboard.app.forms import LoginForm, RegistrationForm, EmailForm, PasswordForm
from dashboard.app.models import User
from werkzeug.urls import url_parse
from dashboard.app import app, db
from dashboard.app.token import generate_confirmation_token, confirm_token
from dashboard.app.email import send_email, send_password_reset_email
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from dashboard.app.signals import new_user_registered


@account_bp.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('account.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home.index')
        return redirect(next_page)
    return render_template('account/login.html', title='Sign In', form=form)

@account_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home.index'))

@account_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.active = False
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(user.email)

        confirm_url = url_for('account.confirm_email', token=token, _external=True)
        html = render_template('email/activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email([user.email], subject, html)

        login_user(user)
        flash('Congratulations, you are now a registered user! Please go to your email and confirm the email address to proceed','success')
        return redirect(url_for('account.unconfirmed'))
    return render_template('account/register.html', title='Register', form=form)


@account_bp.route('/confirm/<token>')
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.active:
        flash('Account already confirmed. Welcome.', 'success')
    else:
        user.active = True
        user.email_confirmed_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
        new_user_registered.send('account', user_id=user.id)

    return redirect(url_for('home.index'))

@account_bp.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.active:
        return redirect(url_for('index'))
    resend_url = url_for("account.resend_confirmation")
    flash(f'Please confirm your account! <a href="{resend_url}" class="alert-link">click here to resend confirmation</a>', 'warning')
    return render_template('account/unconfirmed.html')

@account_bp.route("/resend_confirmation")
@login_required
def resend_confirmation():
    if current_user.active:
        return redirect(url_for('home.index'))
    token = generate_confirmation_token(current_user.email)

    confirm_url = url_for('account.confirm_email', token=token, _external=True)
    html = render_template('email/activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash(f"confirmation for {current_user.username} has been sent to {current_user.email}","success")
    return redirect(url_for("account.unconfirmed"))

@account_bp.route("/reset", methods=['GET', 'POST'])
def reset():
    form = EmailForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return render_template('account/password_reset_email.html', form=form)

        if user.active:
            send_password_reset_email(user.email)
            flash('Please check your email for a password reset link.', 'success')
        else:
            flash('Your email address must be confirmed before attempting a password reset.', 'error')
        return redirect(url_for('account.login'))

    return render_template('account/password_reset_email.html', form=form)


@account_bp.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
        user = User.query.filter_by(email=email).first_or_404()
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('account.login'))


    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return redirect(url_for('account.login'))

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('account.login'))

    form.username.data = user.username
    return render_template('account/reset_password_with_token.html', form=form, token=token)