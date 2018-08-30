from dashboard.app import db

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    msg = db.Column(db.Text())
    levelname = db.Column(db.String(64))
    threadName = db.Column(db.String(64))
    created = db.Column(db.DateTime)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'created_at': self.created.timestamp(),
            'name' : self.name,
            'msg' : self.msg,
            'levelname' : self.levelname,
            'threadName' : self.threadName
        }

    @classmethod
    def searchable_fields(cls):
        """Return fields that can be search for"""
        return [cls.id,cls.name, cls.msg, cls.levelname, cls.threadName]