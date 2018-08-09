from flask import request, render_template, flash, redirect, url_for
from . import bots_bp
from dashboard.app.authorizer import role_required
from dashboard.app.models import Bot
from dashboard.app import app, db, get_bot_status, new_bot_created, destroy_bot
from sqlalchemy import desc
from dashboard.app.forms import CreateBotForm
from flask_login import current_user, login_required
from dashboard.app.authorizer import check_confirmed

@bots_bp.route('/', methods=['GET', 'POST'])
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

    return render_template('account/account.html', form=form, bot = bot)


@bots_bp.route("/all", methods=['GET'])
@role_required('Admin')
def get_bots():
    page = request.args.get('page', 1, type=int)
    bots = Bot.query.order_by(desc(Bot.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template('bots/bots.html', bots=bots)

@bots_bp.route('/<bot_id>', methods=['GET', 'POST'])
@role_required('Admin')
def get_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    owner = bot.owner
    form = CreateBotForm(owner)
    if form.validate_on_submit():
        api_key = form.api_key.data
        api_secret = form.api_secret.data
        name = f"{owner.username}_bot"

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

@bots_bp.route('/account/stop/<bot_id>', methods=['GET'])
@login_required
@role_required('Admin')
def stop_bot(bot_id):
    bot = Bot.query.get(bot_id)
    if not bot:
        flash(f"did not find bot with id {bot_id}")
    else:
        destroy_bot.send('account', bot_id=bot_id)
        flash(f"Stopping Bot {bot.name}")
    return redirect(url_for('bots.get_bot', bot_id = bot_id))

@bots_bp.route('/account/delete/<bot_id>', methods=['GET'])
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
    return redirect(url_for('bots.get_bots'))