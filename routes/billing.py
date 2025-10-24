from __future__ import annotations
from flask import Blueprint, request, jsonify, abort
from services.stripe_service import stripe_svc
from models.core_models import Customer, Subscription
from models import db

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")

@billing_bp.post("/create-checkout-session")
def create_checkout():
    body = request.get_json(force=True)
    user_id = body.get("user_id"); price_id = body.get("price_id")
    if not user_id or not price_id:
        abort(400, "user_id and price_id required")
    url = stripe_svc.create_checkout_session(user_id=user_id, price_id=price_id)
    return jsonify({"checkout_url": url})

@billing_bp.post("/create-portal-session")
def create_portal():
    body = request.get_json(force=True)
    user_id = body.get("user_id")
    if not user_id:
        abort(400, "user_id required")
    url = stripe_svc.create_billing_portal(user_id=user_id)
    return jsonify({"portal_url": url})

@billing_bp.post("/webhook")
def webhook():
    sig = request.headers.get("Stripe-Signature")
    payload = request.data
    event = stripe_svc.verify_webhook(payload, sig)
    if not event:
        abort(400)
    t = event["type"]
    data = event.get("data", {}).get("object", {})
    if t == "checkout.session.completed":
        stripe_svc.handle_checkout_completed(data)
    elif t in ("customer.subscription.created","customer.subscription.updated","customer.subscription.deleted"):
        stripe_svc.handle_subscription_change(data)
    return jsonify({"ok": True})