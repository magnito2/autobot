from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from dashboard.app.authorizer import check_confirmed, role_required, authorize
from . import admin_bp
from dashboard.app.models import User, Role, Bot, Log, Feedback
from dashboard.app import app, db
from sqlalchemy import desc

from dashboard.app.forms import NewEmailForm
from dashboard.app.email import send_email

@admin_bp.route('/')
@login_required
@check_confirmed
def dashboard():
    if authorize('Admin'):
        users = User.query.order_by(desc(User.created_at)).limit(5)
        bots = Bot.query.order_by(desc(Bot.created_at)).limit(5)
        users_count = len(User.query.all())
        bots_count = len(Bot.query.all())
        debug_logs = Log.query.filter_by(levelname='DEBUG').limit(5)
        info_logs = Log.query.filter_by(levelname='INFO').limit(5)
        error_logs = Log.query.filter_by(levelname='ERROR').limit(5)

        searchable = False

        return render_template('admin/admin_dashboard.html', title = 'Admin', users=users, bots=bots, users_count = users_count,
                               bots_count = bots_count, debug_logs = debug_logs, info_logs = info_logs, error_logs = error_logs,
                               searchable = searchable)
    bot = current_user.bots.first()
    return render_template("admin/dashboard.html", title ='AUTOBOTCLOUD', bot=bot)

@admin_bp.route("/roles", methods=['GET','POST'])
@role_required('Admin')
def roles():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(desc(User.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    admin_role = Role.query.filter_by(name='Admin').first()
    return render_template('admin/roles.html', users = users, admin_role = admin_role)

@admin_bp.route("/roles/<user_id>", methods=['GET','POST'])
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

@admin_bp.route("/feedback")
@role_required('Admin')
def feedbacks():
    page = request.args.get('page', 1, type=int)
    feedbacks = Feedback.query.order_by(desc(Feedback.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template('feedback/index.html', feedbacks = feedbacks)

@admin_bp.route("/feedback/<feedback_id>")
@role_required('Admin')
def show_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    return render_template("feedback/show.html", feedback = feedback)


@admin_bp.route("/email", methods=['GET', 'POST'])
@role_required("Admin")
def send_new_email():
    email = request.args.get("email")
    subject = request.args.get("subject")
    form = NewEmailForm()
    if form.validate_on_submit():
        email = form.email.data
        subject = form.subject.data
        body = render_template("email/new_email.html", body = form.body.data)
        send_email([email], subject, body)
        flash("your email has been sent", "success")
        return redirect(url_for("admin.send_new_email"))
    if email:
        form.email.data = email
    if subject:
        form.subject.data = subject
    return render_template("admin/new_email.html", form=form)