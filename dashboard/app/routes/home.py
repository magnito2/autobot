from dashboard.app.routes import home_bp
from flask import render_template, jsonify
from dashboard.app import db
from dashboard.app.forms import FeedbackForm
from dashboard.app.models import Feedback

@home_bp.route("/")
@home_bp.route("/index")
def index():
    return render_template("home/index.html")

@home_bp.route("/feedback", methods=['POST'])
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
        #flash("your message has been sent to us, we'll reply", 'success')
        return jsonify("your message has been sent to us, we'll reply", 'success')
    else:
        return jsonify("sorry, we didn't quite capture that")



@home_bp.route("/faq")
def faq():
    return render_template("home/faq.html")