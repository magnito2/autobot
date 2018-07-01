from flask import render_template, flash, redirect, url_for, request, abort
from dashboard.app import app, db
from dashboard.app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateBotForm, SettingsForm
from flask_login import current_user, login_user, logout_user, login_required
from dashboard.app.models import User, Bot, Role
from werkzeug.urls import url_parse
from datetime import datetime
import configparser
from .token import generate_confirmation_token, confirm_token

from dashboard.app import config_changed, new_bot_created, get_bot_status, destroy_bot
from .authorizer import role_required, check_confirmed
from .email import send_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route('/dashboard')
@login_required
@check_confirmed
def dashboard():
    return render_template("dashboard.html", title = 'AUTOBOTCLOUD')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.active = False
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(user.email)

        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        login_user(user)
        flash('Congratulations, you are now a registered user! Please go to your email and confirm the email address to proceed','success')
        return redirect(url_for('unconfirmed'))
    return render_template('register.html', title='Register', form=form)

@app.route('/account', methods=['GET', 'POST'])
@login_required
@check_confirmed
def account(bot_id = None):
    if bot_id:
        bot = Bot.query.get_or_404(bot_id)
    else:
        bot = current_user.bots.first()
    bots = Bot.query.all()

    form = CreateBotForm(current_user)
    if form.validate_on_submit():
        api_key = form.api_key.data
        api_secret = form.api_secret.data
        name = f"{current_user.username}_bot"
        if not bot:
            bot = Bot(name=name, api_key=api_key, api_secret=api_secret, owner=current_user)
            db.session.add(bot)
        else:
            bot.api_key = api_key
            bot.api_secret = api_secret

        db.session.commit()
        print("attempting to emit create bot event")
        new_bot_created.send('account', bot_id = bot.id)
        flash("Congratulations, you API KEY and SECRET have been added", "success")
        flash("Trading will begin on your account now, until trial period expires")

    if bot:
        form.api_key.data = bot.api_key
        form.api_secret.data = bot.api_secret
        get_bot_status.send('account', bot_id=bot.id)

    return render_template('account.html', form=form, bots = bots, bot = bot)

@app.route('/account/stop/<bot_id>', methods=['GET'])
@login_required
@role_required('Admin')
def stop_bot(bot_id):
    bot = Bot.query.get(bot_id)
    if not bot:
        flash(f"did not find bot with id {bot_id}")
    else:
        destroy_bot.send('account', bot_id=bot_id)
        flash(f"Stopping Bot {bot.name}")
    return redirect("/account")

@app.route('/account/delete/<bot_id>', methods=['GET'])
@login_required
@role_required('Admin')
def delete_bot(bot_id):
    bot = Bot.query.get(bot_id)
    if not bot:
        flash(f"did not find bot with id {bot_id}")
    else:
        db.session.delete(bot)
        db.session.commit()
        flash(f"Delete bot named {bot.name}", 'warning')
    return redirect("/account")

@app.route('/users')
@role_required('Admin')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    bot = user.bots.first()
    return render_template('user.html', user=user, bot = bot)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/settings',  methods=['GET', 'POST'])
@role_required('Admin')
def settings():
    form = SettingsForm()
    config = configparser.ConfigParser()
    if form.validate_on_submit():
        symbol = form.symbol.data
        time_frame = form.time_frame.data
        brick_size = form.brick_size.data
        sma = form.sma.data
        config.read("config.ini")
        config['default'] = {'symbol' : symbol, 'time_frame' : time_frame, 'brick_size' : brick_size, 'sma' : sma}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("emitting event config changed")
        config_changed.send('settings')

    config.read('config.ini')
    form.brick_size.data = config['default']['brick_size']
    form.time_frame.data = config['default']['time_frame']
    form.symbol.data = config['default']['symbol']
    form.sma.data = config['default']['sma']
    return render_template('settings.html', form=form)

@app.route("/roles", methods=['GET','POST'])
@role_required('Admin')
def roles():
    users = User.query.all()
    admin_role = Role.query.filter_by(name='Admin').first()
    return render_template('roles.html', users = users, admin_role = admin_role)

@app.route("/roles/admin/<user_id>", methods=['GET','POST'])
@role_required('Admin')
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role in user.roles:
        user.roles.remove(admin_role)
        flash(f"{user.username} is no longer admin","success")
    else:
        user.roles.append(admin_role)
        flash(f"{user.username} is now admin","warning")
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("roles"))

@app.route("/bot", methods=['GET'])
@role_required('Admin')
def get_bots():
    bots = Bot.query.all()
    return render_template('bots.html', bots=bots)

@app.route('/bot/<bot_id>', methods=['GET', 'POST'])
@role_required('Admin')
def get_bot(bot_id):
    return account(bot_id)

@app.route('/confirm/<token>')
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
    return redirect(url_for('index'))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.active:
        return redirect(url_for('index'))
    resend_url = url_for("resend_confirmation")
    flash(f'Please confirm your account! <a href="{resend_url}" class="alert-link">click here to resend confirmation</a>', 'warning')
    return render_template('unconfirmed.html')

@app.route("/resend_confirmation")
@login_required
def resend_confirmation():
    if current_user.active:
        return redirect(url_for('index'))
    token = generate_confirmation_token(current_user.email)

    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash(f"confirmation for {current_user.username} has been sent to {current_user.email}","success")
    return redirect(url_for("unconfirmed"))
