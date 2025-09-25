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
    if token:
        resp.set_cookie(name, token, httponly=True, secure=False, samesite="Lax", max_age=60*60*24*7, path="/")
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
    u = User(email=email, password_hash=bcrypt.hash(password), name=name)
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
