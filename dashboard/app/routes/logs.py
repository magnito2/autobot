from flask import render_template, redirect, url_for, flash, request, jsonify
from dashboard.app.models import Log, Bot, User
from . import log_bp
from dashboard.app.authorizer import role_required
from sqlalchemy import desc, or_
from dashboard.app import app
from dashboard.app.forms import SearchForm

@log_bp.route("/")
@role_required('Admin')
def index():
    page = request.args.get('page', 1, type=int)
    logs = Log.query.order_by(desc(Log.created)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    form = SearchForm()
    search_url = url_for('logs.search')
    return render_template('logs/index.html', logs = logs, searchable = True, form = form, search_url = search_url)

@log_bp.route("/search", methods=['GET','POST'])
@role_required('Admin')
def search():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    search_value = request.args.get('search_value', type=str)
    if form.validate_on_submit():
        search_value = form.search_value.data
    logs = Log.query.filter(or_((Log.threadName.like(f'%{search_value}%')), (Log.msg.like(f'%{search_value}%')),(Log.levelname.like(f'%{search_value}%'))))\
        .order_by(desc(Log.created)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    search_url = url_for('logs.search')
    if request.is_json:
        pass
    return render_template('logs/index.html', logs = logs, searchable = True, form = form, search_url = search_url, search_value = search_value)