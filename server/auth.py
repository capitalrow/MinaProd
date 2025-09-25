import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, make_response
from argon2 import PasswordHasher
from itsdangerous import URLSafeTimedSerializer, BadSignature
from .models import db, User
from .mail import send_mail

bp_auth = Blueprint("auth", __name__, url_prefix="/api/auth")
_ph = PasswordHasher()

def _sign(payload: dict, ttl_seconds: int):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = s.dumps(payload)
    return token, datetime.utcnow() + timedelta(seconds=ttl_seconds)

def _verify(token: str, max_age: int):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.loads(token, max_age=max_age)

def _set_cookie(resp, name, value, max_age, httponly=True):
    resp.set_cookie(
        name, value, max_age=max_age,
        secure=current_app.config["COOKIE_SECURE"], httponly=httponly,
        samesite=current_app.config["COOKIE_SAMESITE"], path="/",
    )

def _clear_cookie(resp, name):
    resp.delete_cookie(name, path="/")

def _csrf_issue(resp):
    token = secrets.token_urlsafe(24)
    _set_cookie(resp, current_app.config["CSRF_COOKIE_NAME"], token, 60*60*24*14, httponly=False)
    return token

def _csrf_check():
    c = request.cookies.get(current_app.config["CSRF_COOKIE_NAME"])
    h = request.headers.get("X-CSRF-Token")
    return c and h and c == h

@bp_auth.post("/register")
def register():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    pw = data.get("password") or ""
    name = (data.get("name") or "").strip()
    if not email or not pw:
        return jsonify(ok=False, code="bad_request", message="Email and password required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(ok=False, code="exists", message="Email already registered"), 409

    user = User(email=email, password_hash=_ph.hash(pw), name=name)
    db.session.add(user); db.session.commit()

    # Send verify email
    vtoken, _ = _sign({"uid": user.id, "t": "verify"}, 7*24*3600)
    verify_url = f'{current_app.config["PUBLIC_BASE_URL"]}/app#//verify?token={vtoken}'
    try:
        send_mail(email, "Verify your Mina email",
                  f"Hi {name or email},\n\nPlease verify your email:\n{verify_url}\n\n— Mina")
    except Exception as e:
        # Do not block registration; log server-side in real deploy
        pass

    resp = make_response(jsonify(ok=True, user={"id": user.id, "email": user.email, "name": user.name}))
    _csrf_issue(resp)
    access, _ = _sign({"uid": user.id, "t": "access"}, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    refresh, _ = _sign({"uid": user.id, "t": "refresh"}, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
    _set_cookie(resp, current_app.config["ACCESS_COOKIE_NAME"], access, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    _set_cookie(resp, current_app.config["REFRESH_COOKIE_NAME"], refresh, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
    return resp

@bp_auth.post("/login")
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    pw = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user: return jsonify(ok=False, code="unauthorized", message="Invalid credentials"), 401
    try: _ph.verify(user.password_hash, pw)
    except Exception: return jsonify(ok=False, code="unauthorized", message="Invalid credentials"), 401

    resp = make_response(jsonify(ok=True, user={"id": user.id, "email": user.email, "name": user.name, "email_verified": user.email_verified}))
    _csrf_issue(resp)
    access, _ = _sign({"uid": user.id, "t": "access"}, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    refresh, _ = _sign({"uid": user.id, "t": "refresh"}, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
    _set_cookie(resp, current_app.config["ACCESS_COOKIE_NAME"], access, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    _set_cookie(resp, current_app.config["REFRESH_COOKIE_NAME"], refresh, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
    return resp

@bp_auth.post("/logout")
def logout():
    if not _csrf_check():
        return jsonify(ok=False, code="csrf", message="CSRF token missing/invalid"), 400
    resp = make_response(jsonify(ok=True))
    _clear_cookie(resp, current_app.config["ACCESS_COOKIE_NAME"])
    _clear_cookie(resp, current_app.config["REFRESH_COOKIE_NAME"])
    _clear_cookie(resp, current_app.config["CSRF_COOKIE_NAME"])
    return resp

@bp_auth.get("/me")
def me():
    uid = None
    tok = request.cookies.get(current_app.config["ACCESS_COOKIE_NAME"])
    if tok:
        try:
            d = _verify(tok, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
            if d.get("t") == "access": uid = d["uid"]
        except Exception: pass
    if not uid:
        r = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
        if r:
            try:
                d = _verify(r, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
                if d.get("t") == "refresh": uid = d["uid"]
            except Exception: pass
    if not uid: return jsonify(ok=False, code="unauthorized"), 401
    user = User.query.get(uid)
    if not user: return jsonify(ok=False, code="not_found"), 404
    return jsonify(ok=True, user={"id": user.id, "email": user.email, "name": user.name, "tz": user.tz, "email_verified": user.email_verified})

@bp_auth.post("/refresh")
def refresh():
    r = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
    if not r: return jsonify(ok=False, code="unauthorized"), 401
    try:
        d = _verify(r, int(current_app.config["REFRESH_EXPIRES"].total_seconds()))
        if d.get("t") != "refresh": raise BadSignature("bad type")
    except Exception:
        return jsonify(ok=False, code="unauthorized"), 401
    access, _ = _sign({"uid": d["uid"], "t": "access"}, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    resp = make_response(jsonify(ok=True))
    _set_cookie(resp, current_app.config["ACCESS_COOKIE_NAME"], access, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
    _csrf_issue(resp)
    return resp

@bp_auth.post("/change-password")
def change_password():
    if not _csrf_check(): return jsonify(ok=False, code="csrf"), 400
    uid = None
    tok = request.cookies.get(current_app.config["ACCESS_COOKIE_NAME"])
    if tok:
        try:
            d = _verify(tok, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
            if d.get("t") == "access": uid = d["uid"]
        except Exception: pass
    if not uid: return jsonify(ok=False, code="unauthorized"), 401
    data = request.get_json(force=True) or {}
    old_pw = data.get("old_password") or ""
    new_pw = data.get("new_password") or ""
    if not new_pw: return jsonify(ok=False, code="bad_request", message="New password required"), 400
    user = User.query.get(uid)
    try: _ph.verify(user.password_hash, old_pw)
    except Exception: return jsonify(ok=False, code="unauthorized"), 401
    user.password_hash = _ph.hash(new_pw)
    db.session.commit()
    return jsonify(ok=True)

@bp_auth.post("/request-password-reset")
def request_password_reset():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user:
        token, _ = _sign({"uid": user.id, "t": "pwreset"}, 3600)
        reset_url = f'{current_app.config["PUBLIC_BASE_URL"]}/app#//reset?token={token}'
        send_mail(email, "Reset your Mina password",
                  f"Hi {user.name or email},\n\nReset your password:\n{reset_url}\n\n— Mina")
    return jsonify(ok=True)

@bp_auth.post("/reset-password")
def reset_password():
    data = request.get_json(force=True) or {}
    token = data.get("token") or ""
    new_pw = data.get("new_password") or ""
    if not token or not new_pw: return jsonify(ok=False, code="bad_request"), 400
    try:
        payload = _verify(token, 3600)
        if payload.get("t") != "pwreset": raise BadSignature("bad type")
    except Exception:
        return jsonify(ok=False, code="unauthorized"), 401
    user = User.query.get(payload["uid"])
    if not user: return jsonify(ok=False, code="not_found"), 404
    user.password_hash = _ph.hash(new_pw)
    db.session.commit()
    return jsonify(ok=True)

@bp_auth.post("/verify-email")
def verify_email():
    data = request.get_json(force=True) or {}
    token = data.get("token") or ""
    if not token: return jsonify(ok=False, code="bad_request"), 400
    try:
        payload = _verify(token, 7*24*3600)
        if payload.get("t") != "verify": raise BadSignature("bad type")
    except Exception:
        return jsonify(ok=False, code="unauthorized"), 401
    user = User.query.get(payload["uid"])
    if not user: return jsonify(ok=False, code="not_found"), 404
    user.email_verified = True
    db.session.commit()
    return jsonify(ok=True)