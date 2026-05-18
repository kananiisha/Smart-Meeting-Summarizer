from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    summaries = db.relationship('MeetingSummary', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class MeetingSummary(db.Model):
    __tablename__ = 'meeting_summaries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Meeting metadata
    title = db.Column(db.String(200), nullable=False, default='Untitled Meeting')
    input_type = db.Column(db.String(20), nullable=False)  # 'audio' or 'transcript'
    original_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Content
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    action_items = db.Column(db.Text, nullable=True)   # JSON string
    key_decisions = db.Column(db.Text, nullable=True)  # JSON string

    # Processing status
    status = db.Column(db.String(20), default='pending')  # pending, processing, done, error
    error_message = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<MeetingSummary {self.title} by user {self.user_id}>'
