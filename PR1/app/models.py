from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_team_player = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opponent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.Integer, nullable=False)  # 0-9 for 10:00 to 19:00
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, refused

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('reservations', lazy=True))
    opponent = db.relationship('User', foreign_keys=[opponent_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

