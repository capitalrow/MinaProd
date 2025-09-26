from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app, make_response
from passlib.hash import bcrypt
import jwt
from models import db, User

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

def _jwt_create(payload: dict):
    exp = datetime.now(timezone.utc) + timedelta(minutes=current_app.config["JWT_EXPIRE_MINUTES"])
    payload = {**payload, "exp": exp}
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token

def _jwt_read(token: str):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

def _cookie(resp, token):
    name = current_app.config["JWT_COOKIE_NAME"]
    # Secure cookie configuration for production
    if token:
        resp.set_cookie(name, token, httponly=True, secure=not current_app.debug, samesite="Strict", max_age=60*60*24*7, path="/")
    else:
        resp.delete_cookie(name, path="/")
    return resp

@bp_auth.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = data.get("name") or ""
    if not email or not password:
        return jsonify(ok=False, error="email and password required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(ok=False, error="email_already_exists"), 409
    u = User()
    u.email = email
    u.password_hash = bcrypt.hash(password)
    u.name = name
    db.session.add(u)
    db.session.commit()
    token = _jwt_create({"uid": u.id, "email": u.email})
    resp = make_response(jsonify(ok=True, user={"id":u.id,"email":u.email,"name":u.name}))
    return _cookie(resp, token)

@bp_auth.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    u = User.query.filter_by(email=email).first()
    if not u or not bcrypt.verify(password, u.password_hash):
        return jsonify(ok=False, error="invalid_credentials"), 401
    token = _jwt_create({"uid": u.id, "email": u.email})
    resp = make_response(jsonify(ok=True, user={"id":u.id,"email":u.email,"name":u.name}))
    return _cookie(resp, token)

@bp_auth.route("/me", methods=["GET"])
def me():
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if not token:
        return jsonify(ok=False, user=None), 200
    try:
        payload = _jwt_read(token)
    except Exception:
        return jsonify(ok=False, user=None), 200
    u = User.query.get(payload.get("uid"))
    if not u:
        return jsonify(ok=False, user=None), 200
    return jsonify(ok=True, user={"id":u.id,"email":u.email,"name":u.name})

@bp_auth.route("/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify(ok=True))
    return _cookie(resp, None)

@bp_auth.route("/change-password", methods=["POST"])
def change_password():
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if not token:
        return jsonify(ok=False, error="authentication_required"), 401
    try:
        payload = _jwt_read(token)
    except Exception:
        return jsonify(ok=False, error="invalid_token"), 401
    
    data = request.get_json(force=True)
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    
    if not current_password or not new_password:
        return jsonify(ok=False, error="current and new password required"), 400
    
    if len(new_password) < 8:
        return jsonify(ok=False, error="password must be at least 8 characters"), 400
    
    u = User.query.get(payload.get("uid"))
    if not u or not bcrypt.verify(current_password, u.password_hash):
        return jsonify(ok=False, error="invalid_current_password"), 401
    
    u.password_hash = bcrypt.hash(new_password)
    db.session.commit()
    return jsonify(ok=True)

@bp_auth.route("/request-reset", methods=["POST"])
def request_reset():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    
    if not email:
        return jsonify(ok=False, error="email required"), 400
    
    # Always return success for security (don't reveal if email exists)
    u = User.query.filter_by(email=email).first()
    if u:
        # In production, send email with reset token
        # For now, just log the token (development only)
        reset_token = _jwt_create({"uid": u.id, "purpose": "reset", "email": u.email})
        print(f"[DEV] Password reset token for {email}: {reset_token}")
    
    return jsonify(ok=True, message="If email exists, reset link sent")

@bp_auth.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(force=True)
    token = data.get("token") or ""
    password = data.get("password") or ""
    
    if not token or not password:
        return jsonify(ok=False, error="token and password required"), 400
    
    if len(password) < 8:
        return jsonify(ok=False, error="password must be at least 8 characters"), 400
    
    try:
        payload = _jwt_read(token)
        if payload.get("purpose") != "reset":
            raise Exception("invalid purpose")
    except Exception:
        return jsonify(ok=False, error="invalid or expired token"), 400
    
    u = User.query.get(payload.get("uid"))
    if not u:
        return jsonify(ok=False, error="user not found"), 400
    
    u.password_hash = bcrypt.hash(password)
    db.session.commit()
    return jsonify(ok=True)

@bp_auth.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json(force=True)
    token = data.get("token") or ""
    
    if not token:
        return jsonify(ok=False, error="token required"), 400
    
    try:
        payload = _jwt_read(token)
        if payload.get("purpose") != "verify":
            raise Exception("invalid purpose")
    except Exception:
        return jsonify(ok=False, error="invalid or expired token"), 400
    
    u = User.query.get(payload.get("uid"))
    if not u:
        return jsonify(ok=False, error="user not found"), 400
    
    # In a full implementation, you'd have an email_verified field
    # For now, just return success
    return jsonify(ok=True, message="Email verified successfully")
