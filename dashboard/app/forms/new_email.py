from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_pagedown.fields import PageDownField

class NewEmailForm(FlaskForm):
    email = StringField('to', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[])
    body = PageDownField('Body', validators=[DataRequired()])
    submit = SubmitField('Submit')
