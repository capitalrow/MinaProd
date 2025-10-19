from __future__ import annotations
import os
import stripe
from typing import Optional
from models.core_models import Customer, Subscription
from extensions import db

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

class StripeService:
    def _ensure_customer(self, user_id: str) -> Customer:
        cust = Customer.query.filter_by(user_id=user_id).first()
        if cust and cust.stripe_customer_id:
            return cust
        sc = stripe.Customer.create(metadata={"user_id": user_id})
        if not cust:
            cust = Customer(user_id=user_id, stripe_customer_id=sc["id"])
            db.session.add(cust)
        else:
            cust.stripe_customer_id = sc["id"]
        db.session.commit()
        return cust

    def create_checkout_session(self, user_id: str, price_id: str) -> str:
        cust = self._ensure_customer(user_id)
        sess = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer=cust.stripe_customer_id,
            success_url=os.getenv("BILLING_SUCCESS_URL","https://example.com/success"),
            cancel_url=os.getenv("BILLING_CANCEL_URL","https://example.com/cancel"),
        )
        return sess["url"]

    def create_billing_portal(self, user_id: str) -> str:
        cust = self._ensure_customer(user_id)
        sess = stripe.billing_portal.Session.create(
            customer=cust.stripe_customer_id,
            return_url=os.getenv("BILLING_PORTAL_RETURN_URL","https://example.com/account")
        )
        return sess["url"]

    def verify_webhook(self, payload: bytes, sig_header: Optional[str]):
        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        try:
            return stripe.Webhook.construct_event(payload, sig_header, secret)
        except Exception:
            return None

    def handle_checkout_completed(self, data: dict):
        customer_id = data.get("customer")
        cust = Customer.query.filter_by(stripe_customer_id=customer_id).first()
        if not cust: return
        # link subscription if provided
        sub_id = data.get("subscription")
        if sub_id:
            self._upsert_subscription(cust, sub_id, "active")

    def handle_subscription_change(self, data: dict):
        customer_id = data.get("customer"); status = data.get("status"); sub_id = data.get("id")
        cust = Customer.query.filter_by(stripe_customer_id=customer_id).first()
        if not cust or not sub_id: return
        self._upsert_subscription(cust, sub_id, status or "active")

    def _upsert_subscription(self, cust: Customer, sub_id: str, status: str):
        s = Subscription.query.filter_by(stripe_subscription_id=sub_id).first()
        if not s:
            s = Subscription(customer_id=cust.id, stripe_subscription_id=sub_id, status=status)
            db.session.add(s)
        else:
            s.status = status
        db.session.commit()

stripe_svc = StripeService()