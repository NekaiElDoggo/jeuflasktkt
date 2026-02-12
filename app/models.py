from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    currency = db.Column(db.Integer, default=1000)
    pity_state = db.Column(db.Text, default='{}')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(40), default='character')
    rarity = db.Column(db.Integer, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    pool_tag = db.Column(db.String(80), default='standard')
    metadata_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class InventoryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    count = db.Column(db.Integer, default=1)
    acquired_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PullRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pool_tag = db.Column(db.String(80), nullable=False)
    num_pulls = db.Column(db.Integer, nullable=False)
    results = db.Column(db.Text, nullable=False)  # store JSON string
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cost = db.Column(db.Integer, default=0)
