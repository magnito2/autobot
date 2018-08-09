from flask import flash, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from dashboard.app import app, db
from dashboard.app.forms import PaymentForm
from dashboard.app.models import Payment, User
import configparser
from dashboard import pyCoinPayments
from dashboard.app.authorizer import role_required, check_hmac
from datetime import timedelta
from sqlalchemy import desc
from . import payment_bp

@payment_bp.route("/", methods=['GET','POST'])
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
        IPN_URL = url_for("payments.confirm_payment", _external=True)
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


@payment_bp.route("/confirm", methods=['POST'])
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

@payment_bp.route("/activate")
def activate():
    flash("make payment for account to be activated")
    return redirect(url_for('payments.payment'))

@payment_bp.route("/all", methods=['GET'])
@role_required('Admin')
def view_payments():
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.order_by(desc(Payment.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template("payments/view.html", payments=payments)