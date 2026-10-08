"""DATABASE LAYER: the only place that talks to the tables.

Routes and services never write SQLAlchemy queries; they call these functions.
If you later move from SQLite to PostgreSQL, only this file (and config) changes.
"""
import secrets
from statistics import median

from sqlalchemy import func

from extensions import db
from models import Child, Feedback, Reading, User


# ---------- users ----------
def get_user_by_email(email):
    return User.query.filter_by(email=email.strip().lower()).first()


def get_user(user_id):
    return db.session.get(User, user_id)


def create_user(name, email, password):
    u = User(name=name.strip(), email=email.strip().lower())
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u


# ---------- children ----------
def get_child(child_id):
    return db.session.get(Child, child_id)


def get_child_by_device_key(key):
    return Child.query.filter_by(device_key=key).first()


def list_children(owner_id):
    return Child.query.filter_by(owner_id=owner_id).order_by(Child.id).all()


def create_child(owner_id, name):
    c = Child(owner_id=owner_id, name=name.strip())
    db.session.add(c)
    db.session.commit()
    return c


def rename_child(child, name):
    child.name = name.strip()
    db.session.commit()
    return child


def rotate_device_key(child):
    """Issue a new key (the old one stops working immediately)."""
    child.device_key = secrets.token_hex(16)
    db.session.commit()
    return child


def delete_child(child):
    """Deletes the child and all their readings; feedback is removed first (no cascade on it)."""
    Feedback.query.filter_by(child_id=child.id).delete()
    db.session.delete(child)
    db.session.commit()


# ---------- readings ----------
def add_reading(**fields):
    r = Reading(**fields)
    db.session.add(r)
    db.session.commit()
    return r


def last_readings(child_id, limit):
    """Newest first."""
    return (Reading.query.filter_by(child_id=child_id)
            .order_by(Reading.id.desc()).limit(limit).all())


def latest_reading(child_id):
    return Reading.query.filter_by(child_id=child_id).order_by(Reading.id.desc()).first()


def get_reading(reading_id):
    return db.session.get(Reading, reading_id)


def heart_rate_baseline(child_id, window, min_readings):
    """The child's 'usual' HR = median of the last `window` readings (None while warming up)."""
    rows = (db.session.query(Reading.heart_rate).filter_by(child_id=child_id)
            .order_by(Reading.id.desc()).limit(window).all())
    values = [r[0] for r in rows]
    return median(values) if len(values) >= min_readings else None


def summary_counts(child_id):
    base = Reading.query.filter_by(child_id=child_id)
    total = base.count()
    calm = base.filter_by(status="calm").count()
    avg_hr = db.session.query(func.avg(Reading.heart_rate)).filter_by(child_id=child_id).scalar() or 0
    return total, calm, float(avg_hr)


# ---------- feedback ----------
def add_feedback(reading_id, child_id, user_id, correct):
    f = Feedback(reading_id=reading_id, child_id=child_id, user_id=user_id, correct=correct)
    db.session.add(f)
    db.session.commit()
    return f


def feedback_counts(child_id):
    q = Feedback.query.filter_by(child_id=child_id)
    return q.filter_by(correct=True).count(), q.filter_by(correct=False).count()


def list_feedback(child_id):
    return Feedback.query.filter_by(child_id=child_id).order_by(Feedback.id).all()
