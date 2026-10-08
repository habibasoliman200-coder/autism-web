"""Authentication.

Two kinds of callers, two mechanisms:
  1) Dashboard / mobile app (a parent)  -> header  Authorization: Bearer <JWT>
  2) The ESP32 wristband                -> header  X-Device-Key: <child.device_key>
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

import repositories as repo


def make_token(user):
    exp = datetime.now(timezone.utc) + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"])
    return jwt.encode({"sub": str(user.id), "exp": exp}, current_app.config["SECRET_KEY"], algorithm="HS256")


def _error(message, code):
    return jsonify({"status": "error", "message": message}), code


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return _error("Missing token. Send  Authorization: Bearer <token>", 401)
        try:
            payload = jwt.decode(header[7:], current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user = repo.get_user(int(payload["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            return _error("Invalid or expired token", 401)
        if user is None:
            return _error("User no longer exists", 401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper


def device_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-Device-Key", "")
        child = repo.get_child_by_device_key(key) if key else None
        if child is None:
            return _error("Unknown or missing X-Device-Key", 401)
        g.child = child
        return fn(*args, **kwargs)
    return wrapper


def own_child_required(fn):
    """Use after @login_required on routes that contain <int:child_id>.
    A parent can only see HIS OWN children."""
    @wraps(fn)
    def wrapper(*args, child_id, **kwargs):
        child = repo.get_child(child_id)
        if child is None or child.owner_id != g.user.id:
            return _error("Child not found", 404)   # 404 on purpose: do not reveal it exists
        g.child = child
        return fn(*args, child_id=child_id, **kwargs)
    return wrapper
