from dashboard.app import db

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    msg = db.Column(db.Text())
    levelname = db.Column(db.String(64))
    threadName = db.Column(db.String(64))
    created = db.Column(db.DateTime)