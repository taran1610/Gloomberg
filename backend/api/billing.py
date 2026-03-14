import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from config import get_settings
from services.auth import (
    require_auth,
    get_user_by_stripe_customer,
    set_user_plan,
    set_stripe_customer,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _stripe():
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key
    return stripe


def _is_configured() -> bool:
    s = get_settings()
    return bool(s.stripe_secret_key and s.stripe_price_id_pro)


@router.get("/status")
async def billing_status():
    return {"configured": _is_configured()}


@router.post("/create-checkout")
async def create_checkout(user: dict = Depends(require_auth)):
    s = _stripe()
    settings = get_settings()

    if not _is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    if user.get("plan") == "pro":
        raise HTTPException(status_code=400, detail="Already on Pro plan")

    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        customer = s.Customer.create(email=user["email"], metadata={"user_id": user["id"]})
        customer_id = customer.id
        set_stripe_customer(user["id"], customer_id)

    session = s.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
        success_url=f"{settings.frontend_url}/pricing?success=true",
        cancel_url=f"{settings.frontend_url}/pricing?canceled=true",
        metadata={"user_id": user["id"]},
    )

    return {"checkout_url": session.url}


@router.post("/portal")
async def customer_portal(user: dict = Depends(require_auth)):
    s = _stripe()
    settings = get_settings()

    if not _is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    session = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/pricing",
    )
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    settings = get_settings()
    s = _stripe()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = s.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    etype = event["type"]
    obj = event["data"]["object"]

    if etype in (
        "customer.subscription.created",
        "customer.subscription.updated",
    ):
        customer_id = obj.get("customer")
        status = obj.get("status")
        user = get_user_by_stripe_customer(customer_id)
        if user:
            plan = "pro" if status == "active" else "free"
            set_user_plan(user["id"], plan)

    elif etype == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        user = get_user_by_stripe_customer(customer_id)
        if user:
            set_user_plan(user["id"], "free")

    return {"received": True}
