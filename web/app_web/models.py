from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app_web import database

class Profile(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(255), unique=True, nullable=False)
    last_parsed = database.Column(database.DateTime)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    errors_count = database.Column(database.Integer, default=0, nullable=False)

    # Relationships
    posts = database.relationship('Post', backref='profile', lazy=True, cascade='all, delete-orphan')
    subscriptions = database.relationship('Subscription', backref='profile', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Profile {self.username}>'


class Post(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    instagram_post_id = database.Column(database.String(255), nullable=False)
    profile_id = database.Column(database.Integer, database.ForeignKey('profile.id'), nullable=False)
    media_type = database.Column(database.String(50))
    is_sent = database.Column(database.Boolean, default=False)
    sent_at = database.Column(database.DateTime)
    sent_to = database.Column(database.String(255))
    is_downloaded = database.Column(database.Boolean, default=False)
    file_path = database.Column(database.String(512))
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    errors_count = database.Column(database.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Post {self.instagram_post_id}>'


class Subscription(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    profile_id = database.Column(database.Integer, database.ForeignKey('profile.id'), nullable=False)
    telegram_user_id = database.Column(database.Integer, database.ForeignKey('telegram_user.id'), nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription telegram_user:{self.telegram_user_id} profile:{self.profile_id}>'


class TelegramUser(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    telegram_id = database.Column(database.String(255), unique=True, nullable=False)
    is_active = database.Column(database.Boolean, default=False, nullable=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)

    subscriptions = database.relationship('Subscription', backref='telegram_user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TelegramUser {self.telegram_id}>'


class AdminUser(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(255), unique=True, nullable=False)
    password_hash = database.Column(database.String(255), nullable=False)
    is_active = database.Column(database.Boolean, default=True)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

