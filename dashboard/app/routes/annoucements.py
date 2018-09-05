from dashboard.app.routes import annoucements_bp
from dashboard.app.authorizer import role_required
from flask import render_template, request, jsonify, abort, flash, redirect, url_for, session
from dashboard.app import app, db
from flask_login import login_required, current_user

from sqlalchemy import desc

from dashboard.app.models import Announcement
from dashboard.app.forms import AnnouncementForm

@annoucements_bp.route("/")
@role_required('Admin')
def index():
    page = request.args.get('page', 1, type=int)
    announcements = Announcement.query.order_by(desc(Announcement.created_at)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    return render_template('announcements/index.html', announcements=announcements)

@annoucements_bp.route("/update")
@login_required
def last_announcement():
    announcement = Announcement.query.order_by(desc(Announcement.id)).first()
    if announcement:
        if 'announcements' not in session:
            print("session object has no announcements")
            session['announcements'] = {}
        if str(current_user.id) not in session['announcements']:
            print("user id not in annoucements")
            session['announcements'][str(current_user.id)] = []
        #if str(announcement.id) not in session['announcements'][str(current_user.id)]:
         #   session['announcements'][str(current_user.id)].append(str(announcement.id))
          #  print(session['announcements'])
        return jsonify(announcement.serialize)
        #abort(404)
    else:
        abort(404)

@annoucements_bp.route("/create", methods=['POST', 'GET'])
@role_required("Admin")
def create():
    form = AnnouncementForm()

    if form.validate_on_submit():
        announcement = Announcement(title=form.title.data, message=form.message.data)
        db.session.add(announcement)
        db.session.commit()
        flash("A new announcement has been created", "success")
        return redirect(url_for("announcements.create"))

    return render_template("announcements/create.html", form=form)

@annoucements_bp.route("/<announcement_id>", methods=['GET', 'POST'])
def show(announcement_id):
    annoucement = Announcement.query.get_or_404(announcement_id)
    return jsonify(annoucement.serialize)