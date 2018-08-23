from dashboard.app.routes import user_bp
from flask_login import login_required, current_user
from flask import redirect, url_for, render_template, request, flash
from dashboard.app.forms import EditProfileForm, SearchForm
from dashboard.app.models import User, Log
from dashboard.app import app, db
from dashboard.app.authorizer import role_required
from sqlalchemy import desc, or_


@user_bp.route('/all')
@role_required('Admin')
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(desc(User.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    search_url = url_for('users.search')
    form = SearchForm()
    return render_template('account/users.html', users=users, searchable = True, search_url = search_url, form=form)

@user_bp.route('/search', methods = ['GET', 'POST'])
@role_required('Admin')
def search():
    search_form = SearchForm()
    page = request.args.get('page', 1, type=int)
    search_value = request.args.get('search_value', type=str)
    if search_form.validate_on_submit():
        search_value = search_form.search_value.data
    users = User.query.filter(or_((User.username.like(f'%{search_value}%')), (User.email.like(f'%{search_value}%')))).\
        order_by(desc(User.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    search_url = url_for('users.search')
    return render_template('account/users.html', users = users, searchable = True, form = search_form, search_url = search_url, search_value = search_value)


@user_bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    bot = user.bots.first()
    logs = Log.query.filter(Log.threadName.like(f'%{bot.name}%')).order_by(desc(Log.created)).limit(10)
    return render_template('account/user.html', user=user, bot = bot, logs=logs)

@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('admin.dashboard', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('account/edit_profile.html', title='Edit Profile',
                           form=form)