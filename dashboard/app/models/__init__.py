from dashboard.app import db
from datetime import datetime
from dashboard.app import login

from .log import Log
from .user import User
from .payment import Payment
from .bot import Bot

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role {}>'.format(self.name)

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class Feedback(db.Model):
    __tablename__='feedbacks'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    subject = db.Column(db.Text())
    message = db.Column(db.Text())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.id} {self.subject} from {self.name}>"

class Announcement(db.Model):
    __tablename__="announcements"
    id=db.Column(db.Integer(), primary_key=True)
    title=db.Column(db.String(64))
    message= db.Column(db.Text())
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Announcement {self.id} {self.title} from {self.created_at}>"

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'created_at': self.created_at.timestamp(),
            'title': self.title,
            'message': self.message
        }

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
