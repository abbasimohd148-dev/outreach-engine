# services/billing.py
# Stripe billing + credit management

import stripe
import os
from utils.db import Database

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLAN_LIMITS = {
    "starter": 200,
    "growth": 1000,
    "agency": 5000,
}

STRIPE_PRICE_IDS = {
    "starter": os.getenv("STRIPE_PRICE_STARTER"),   # $49/mo
    "growth": os.getenv("STRIPE_PRICE_GROWTH"),     # $149/mo
    "agency": os.getenv("STRIPE_PRICE_AGENCY"),     # $399/mo
}


class BillingService:

    def __init__(self, db: Database):
        self.db = db

    async def check_credits(self, user_id: str, needed: int) -> bool:
        """Returns True if user has enough credits for this batch"""
        row = await self.db.fetchrow(
            "SELECT credits_used, credits_limit FROM users WHERE id = $1", user_id
        )
        remaining = row["credits_limit"] - row["credits_used"]
        return remaining >= needed

    async def consume_credits(self, user_id: str, amount: int):
        """Deduct credits after successful enrichment"""
        await self.db.execute("""
            UPDATE users SET credits_used = credits_used + $1 WHERE id = $2
        """, amount, user_id)

    async def reset_monthly_credits(self, user_id: str):
        """Called by Stripe webhook on subscription renewal"""
        row = await self.db.fetchrow("SELECT plan FROM users WHERE id = $1", user_id)
        limit = PLAN_LIMITS.get(row["plan"], 200)
        await self.db.execute("""
            UPDATE users SET credits_used = 0, credits_limit = $1 WHERE id = $2
        """, limit, user_id)

    async def create_checkout_session(self, user_id: str, plan: str, email: str) -> str:
        """Create Stripe checkout session, return URL"""
        price_id = STRIPE_PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"Unknown plan: {plan}")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=email,
            metadata={"user_id": user_id, "plan": plan},
            success_url=f"{os.getenv('APP_URL')}/dashboard?upgraded=true",
            cancel_url=f"{os.getenv('APP_URL')}/pricing",
        )
        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Handle Stripe webhooks:
        - checkout.session.completed → upgrade plan
        - customer.subscription.deleted → downgrade to free
        - invoice.paid → reset monthly credits
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid Stripe signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            plan = session["metadata"]["plan"]
            limit = PLAN_LIMITS.get(plan, 200)
            await self.db.execute("""
                UPDATE users SET 
                    plan = $1, 
                    credits_limit = $2,
                    stripe_customer_id = $3,
                    stripe_subscription_id = $4
                WHERE id = $5
            """, plan, limit, session.get("customer"), session.get("subscription"), user_id)

        elif event["type"] == "invoice.paid":
            # Reset credits on renewal
            customer_id = event["data"]["object"]["customer"]
            row = await self.db.fetchrow(
                "SELECT id FROM users WHERE stripe_customer_id = $1", customer_id
            )
            if row:
                await self.reset_monthly_credits(row["id"])

        elif event["type"] == "customer.subscription.deleted":
            customer_id = event["data"]["object"]["customer"]
            await self.db.execute("""
                UPDATE users SET plan = 'starter', credits_limit = 200 
                WHERE stripe_customer_id = $1
            """, customer_id)
