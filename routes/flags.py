from __future__ import annotations
from flask import Blueprint, request, jsonify, abort
from services.feature_flags import flags, require_flag_admin
from models.core_models import FeatureFlag
from extensions import db

flags_bp = Blueprint("flags", __name__, url_prefix="/flags")

@flags_bp.get("/")
def list_flags():
    return jsonify([f.to_dict() for f in FeatureFlag.query.order_by(FeatureFlag.key).all()])

@flags_bp.post("/")
@require_flag_admin
def upsert_flag():
    body = request.get_json(force=True)
    key = body.get("key"); enabled = bool(body.get("enabled", False)); note = body.get("note")
    if not key:
        abort(400, "key is required")
    flag = FeatureFlag.query.filter_by(key=key).first()
    if not flag:
        flag = FeatureFlag(key=key, enabled=enabled, note=note)
        db.session.add(flag)
    else:
        flag.enabled = enabled; flag.note = note
    db.session.commit()
    flags.invalidate_cache()
    return jsonify(flag.to_dict())

@flags_bp.delete("/<string:key>")
@require_flag_admin
def delete_flag(key: str):
    flag = FeatureFlag.query.filter_by(key=key).first()
    if not flag:
        abort(404)
    db.session.delete(flag); db.session.commit()
    flags.invalidate_cache()
    return jsonify({"deleted": key})