"""Database tables (SQLAlchemy). Database file: instance/calmband.db (SQLite).

users ──< children ──< readings ──< feedback
"""
import secrets
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def _now():
    return datetime.now()


class User(db.Model):
    """A parent / caregiver who logs in to the dashboard."""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=_now)
    children = db.relationship("Child", back_populates="owner", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Child(db.Model):
    """One child = one wristband. device_key is the secret the ESP32 sends."""
    __tablename__ = "children"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    device_key = db.Column(db.String(64), nullable=False, unique=True, index=True,
                           default=lambda: secrets.token_hex(16))
    created_at = db.Column(db.DateTime, default=_now)
    owner = db.relationship("User", back_populates="children")
    readings = db.relationship("Reading", back_populates="child", cascade="all, delete-orphan")

    def to_dict(self, with_key=False):
        d = {"id": self.id, "name": self.name}
        if with_key:
            d["device_key"] = self.device_key
        return d


class Reading(db.Model):
    """One sensor sample (about 1 per second) + the decision made for it."""
    __tablename__ = "readings"
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=_now, index=True)
    heart_rate = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    gsr = db.Column(db.Float, nullable=False)           # skin conductance (EDA)
    acc_x = db.Column(db.Float)                          # accelerometer (needed by the AI model)
    acc_y = db.Column(db.Float)
    acc_z = db.Column(db.Float)
    motion = db.Column(db.Float, nullable=False, default=0.0)  # 0..1
    above_baseline_pct = db.Column(db.Integer, default=0)
    risk = db.Column(db.Float)                           # AI probability 0..1 (null if rules used)
    raw_status = db.Column(db.String(20), default="calm")
    status = db.Column(db.String(20), default="calm")    # smoothed: what the UI shows
    engine = db.Column(db.String(10), default="rules")   # "ai" or "rules"
    device_status = db.Column(db.String(200))
    child = db.relationship("Child", back_populates="readings")

    __table_args__ = (db.Index("ix_readings_child_id_id", "child_id", "id"),)

    def to_dict(self):
        t = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "id": self.id, "child_id": self.child_id, "time": t, "timestamp": t,
            "heart_rate": round(self.heart_rate, 1), "temperature": round(self.temperature, 1),
            "gsr": round(self.gsr, 2), "motion": round(self.motion, 2),
            "above_baseline_pct": self.above_baseline_pct,
            "risk": None if self.risk is None else round(self.risk, 3),
            "status": self.status, "engine": self.engine, "device_status": self.device_status,
        }


class Feedback(db.Model):
    """Parent says: was this alert correct or a false alarm? (future training data)"""
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    reading_id = db.Column(db.Integer, db.ForeignKey("readings.id"), nullable=False, index=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=_now)
