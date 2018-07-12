from flask import render_template, flash, redirect, url_for, request, jsonify
from dashboard.app import app, db
from dashboard.app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateBotForm, SettingsForm, PaymentForm, FeedbackForm, EmailForm, PasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from dashboard.app.models import User, Bot, Role, Payment, Feedback
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
import configparser, os
from .token import generate_confirmation_token, confirm_token
from dashboard.app import config_changed, new_bot_created, get_bot_status, destroy_bot, new_user_registered, new_payment_made
from .authorizer import role_required, check_confirmed, check_hmac
from .email import send_email, send_password_reset_email
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import desc

from dashboard import pyCoinPayments

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route("/")
@app.route("/index")
def index():
    return render_template("home/index.html")

@app.route('/dashboard')
@login_required
@check_confirmed
def dashboard():
    bot = current_user.bots.first()
    return render_template("dashboard.html", title = 'AUTOBOTCLOUD', bot=bot)

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
    return render_template('account/login.html', title='Sign In', form=form)

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
        html = render_template('email/activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email([user.email], subject, html)

        login_user(user)
        flash('Congratulations, you are now a registered user! Please go to your email and confirm the email address to proceed','success')
        return redirect(url_for('unconfirmed'))
    return render_template('account/register.html', title='Register', form=form)

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

    return render_template('account.html', form=form, user=user, bot = bot)

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
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(desc(User.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
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
        dir_path = os.path.dirname(os.path.realpath(''))
        config.read(app.config['CONFIG_INI_FILE'])
        config['default'] = {'symbol' : symbol, 'time_frame' : time_frame, 'brick_size' : brick_size, 'sma' : sma}
        with open(app.config['CONFIG_INI_FILE'], 'w') as configfile:
            config.write(configfile)
        print("emitting event config changed")
        config_changed.send('settings')

    config.read(app.config['CONFIG_INI_FILE'])
    form.brick_size.data = config['default']['brick_size']
    form.time_frame.data = config['default']['time_frame']
    form.symbol.data = config['default']['symbol']
    form.sma.data = config['default']['sma']
    return render_template('settings.html', form=form)

@app.route("/roles", methods=['GET','POST'])
@role_required('Admin')
def roles():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(desc(User.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
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
    page = request.args.get('page', 1, type=int)
    bots = Bot.query.order_by(desc(Bot.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template('bots.html', bots=bots)

@app.route('/bot/<bot_id>', methods=['GET', 'POST'])
@role_required('Admin')
def get_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    owner = bot.owner
    form = CreateBotForm(owner)
    if form.validate_on_submit():
        api_key = form.api_key.data
        api_secret = form.api_secret.data
        name = f"{owner.username}_bot"
        if not bot:
            bot = Bot(name=name, api_key=api_key, api_secret=api_secret, owner=owner)
            db.session.add(bot)
        else:
            bot.api_key = api_key
            bot.api_secret = api_secret

        db.session.commit()
        print("attempting to emit edit bot event")
        new_bot_created.send('edit bot', bot_id=bot.id)
        flash(f"You change API KEY and SECRET for {owner.username}", "success")
        flash("Bot will reset")

    if bot:
        form.api_key.data = bot.api_key
        form.api_secret.data = bot.api_secret
        get_bot_status.send('account', bot_id=bot.id)
    return render_template('bots/bot.html', bot=bot, form=form)

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
        new_user_registered.send('account', user_id=user.id)

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

@app.route("/payment", methods=['GET','POST'])
@login_required
def payment():
    form = PaymentForm()
    config = configparser.ConfigParser()
    bot = current_user.bots.first()
    if form.validate_on_submit():
        currency_2 = form.currency.data
        config.read("config.ini")
        PUBLIC_KEY = app.config['COINSPAYMENT_PUBLIC_KEY']
        SECRET_KEY = app.config['COINSPAYMENT_PRIVATE_KEY']
        IPN_URL = url_for("confirm_payment", _external=True)
        payapi = pyCoinPayments.CryptoPayments(PUBLIC_KEY, SECRET_KEY, IPN_URL)

        params = {
            'amount' : app.config['COINS_PAYMENT_AMOUNT'],
            'currency1' : 'BTC',
            'currency2' : currency_2,
            'buyer_email' : current_user.email,
            'buyer_name' : current_user.username,
            'item_name' : "trading-bot-subscription",
            'item_number' : current_user
        }

        if bot:
            params['item_number'] = bot.id
        trans_resp = payapi.createTransaction(params)
        if not trans_resp['error'] == 'ok':
            flash(trans_resp['error'], 'warning')
        else:
            flash(f'Thank you, please use provided address to make payment, currency is {currency_2}', 'info')
            return render_template("/payments/pay.html", transaction_details = trans_resp['result'], currency_2 = currency_2)

    return render_template("/payments/index.html", form=form)


@app.route("/confirm_payment", methods=['POST'])
@check_hmac
def confirm_payment():
    form = request.form
    data = {
        'ipn_id' : form.get('ipn_id'),
        'txn_id' : form.get('txn_id'),
        'status' : form.get('status'),
        'status_text' : form.get('status_text'),
        'currency1' : form.get('currency1'),
        'currency2' : form.get('currency2'),
        'amount1' : form.get('amount1'),
        'amount2' : form.get('amount2'),
        'fee' : form.get('fee'),
        'buyer_name' : form.get('buyer_name'),
        'email' : form.get('email'),
        'item_name' : form.get('item_name'),
        'item_number' : form.get('item_number'),
        'send_tx' : form.get('send_tx'),
        'recieved_amount' : form.get('recieved_amount'),
        'recieved_confirms' : form.get('recieved_confirms')
    }


    payment = Payment.query.filter_by(txn_id=data['txn_id']).first()
    user = User.query.filter_by(email=data['email']).first()
    params = {}
    for key in data:
        if data[key]:
            params[key] = data[key]
    if not payment:
        payment = Payment(**params)
        print("[+] No existing payments, creating a new payment")
    else:
        for key in params:
            setattr(payment, key, params[key])
        print("[+] Updating the current payment")

    if int(payment.status) > 99 and user:
        bot = user.bots.first()
        if bot and not payment.is_complete:
            bot.expires_at += timedelta(days=30)
            db.session.add(bot)
            payment.is_complete = True

    if user:
        user.payments.append(payment)
        db.session.add(user)
    db.session.add(payment)
    db.session.commit()

    print(f"{payment.status}:{payment.status_text}, {payment.ipn_id} {payment.txn_id}")
    print(payment)

    print("Yeeey, we made it")
    return ('', 204)


@app.route("/feedback", methods=['POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        feedback_info = Feedback(
            name= form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(feedback_info)
        db.session.commit()
        flash("your message has been sent to us, we'll reply", 'success')
        return redirect(url_for("index"))
    else:
        return render_template("contact-form.html", form=form)

@app.route("/reset", methods=['GET', 'POST'])
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
        return redirect(url_for('login'))

    return render_template('account/password_reset_email.html', form=form)


@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
        user = User.query.filter_by(email=email).first_or_404()
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))


    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return redirect(url_for('login'))

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    form.username.data = user.username
    return render_template('account/reset_password_with_token.html', form=form, token=token)

@app.route("/activate")
def activate():
    flash("make payment for account to be activated")
    return redirect(url_for('payment'))

@app.route("/faq")
def faq():
    return render_template("home/faq.html")

@app.route("/view_payments", methods=['GET'])
@role_required('Admin')
def view_payments():
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.order_by(desc(Payment.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template("payments/view.html", payments=payments)