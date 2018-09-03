from dashboard.app import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer(), primary_key=True)
    ipn_id = db.Column(db.String(64), unique=True)
    txn_id = db.Column(db.String(64), unique=True)
    status = db.Column(db.String(64))
    status_text = db.Column(db.String(128))
    currency1 = db.Column(db.String(32))
    currency2 = db.Column(db.String(32))
    amount1 = db.Column(db.Integer())
    amount2 = db.Column(db.Integer())
    fee = db.Column(db.String(50))
    buyer_name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    item_name = db.Column(db.String(64))
    item_number = db.Column(db.String(64))
    send_tx = db.Column(db.String(64))
    recieved_amount = db.Column(db.String(64))
    recieved_confirms = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_complete = db.Column('is_complete', db.Boolean(), nullable=False, server_default='0')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Payment {self.txn_id} {self.amount2} {self.currency2}>"