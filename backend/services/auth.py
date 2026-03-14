import hashlib
import hmac
import os
import time
import base64
import uuid
from datetime import date
from typing import Optional

import jwt
from fastapi import Request, HTTPException

from config import get_settings

# ---------------------------------------------------------------------------
# In-memory stores (swap with database in production)
# ---------------------------------------------------------------------------
_users: dict[str, dict] = {}
_users_by_email: dict[str, str] = {}
_usage: dict[str, dict] = {}

PLAN_LIMITS = {
    "free": {
        "ai_messages_per_day": 10,
        "backtests_per_day": 3,
        "ai_strategy_generator": False,
    },
    "pro": {
        "ai_messages_per_day": 200,
        "backtests_per_day": 50,
        "ai_strategy_generator": True,
    },
}

# ---------------------------------------------------------------------------
# Password helpers (PBKDF2-SHA256, no extra native deps)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt + dk).decode()


def verify_password(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode())
    salt, dk = raw[:16], raw[16:]
    dk2 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(dk, dk2)

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_token(user_id: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + 7 * 24 * 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except Exception:
        return None

# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def register_user(email: str, password: str) -> dict:
    email = email.lower().strip()
    if email in _users_by_email:
        raise ValueError("Email already registered")

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "plan": "free",
        "stripe_customer_id": None,
        "created_at": time.time(),
    }
    _users[user_id] = user
    _users_by_email[email] = user_id
    return user


def authenticate_user(email: str, password: str) -> Optional[dict]:
    email = email.lower().strip()
    user_id = _users_by_email.get(email)
    if not user_id:
        return None
    user = _users[user_id]
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def get_user(user_id: str) -> Optional[dict]:
    return _users.get(user_id)


def get_user_by_stripe_customer(customer_id: str) -> Optional[dict]:
    for user in _users.values():
        if user.get("stripe_customer_id") == customer_id:
            return user
    return None


def set_user_plan(user_id: str, plan: str):
    if user_id in _users:
        _users[user_id]["plan"] = plan


def set_stripe_customer(user_id: str, customer_id: str):
    if user_id in _users:
        _users[user_id]["stripe_customer_id"] = customer_id

# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------

def _today() -> str:
    return date.today().isoformat()


def get_usage(user_id: str) -> dict:
    today = _today()
    usage = _usage.get(user_id)
    if not usage or usage.get("date") != today:
        usage = {"date": today, "ai_messages": 0, "backtests": 0}
        _usage[user_id] = usage
    return usage


def increment_usage(user_id: str, field: str):
    usage = get_usage(user_id)
    usage[field] = usage.get(field, 0) + 1


def get_plan_limits(plan: str) -> dict:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def check_limit(user_id: Optional[str], action: str) -> tuple[bool, str]:
    """Returns (allowed, reason). If no user, allow (unauthenticated = unlimited basic)."""
    if not user_id:
        return True, ""

    user = get_user(user_id)
    plan = user.get("plan", "free") if user else "free"
    limits = get_plan_limits(plan)
    usage = get_usage(user_id)

    if action == "ai_message":
        limit = limits["ai_messages_per_day"]
        if usage.get("ai_messages", 0) >= limit:
            return False, f"Daily AI message limit reached ({limit}/day). Upgrade to Pro for more."
        return True, ""

    if action == "backtest":
        limit = limits["backtests_per_day"]
        if usage.get("backtests", 0) >= limit:
            return False, f"Daily backtest limit reached ({limit}/day). Upgrade to Pro for more."
        return True, ""

    if action == "ai_strategy":
        if not limits["ai_strategy_generator"]:
            return False, "AI Strategy Generator is a Pro feature. Upgrade to unlock."
        return True, ""

    return True, ""

# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user_optional(request: Request) -> Optional[dict]:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    payload = decode_token(auth[7:])
    if not payload:
        return None
    return get_user(payload.get("sub", ""))


async def require_auth(request: Request) -> dict:
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def user_public(user: dict) -> dict:
    """Strip sensitive fields for API responses."""
    limits = get_plan_limits(user.get("plan", "free"))
    usage = get_usage(user["id"])
    return {
        "id": user["id"],
        "email": user["email"],
        "plan": user.get("plan", "free"),
        "usage": {
            "ai_messages": usage.get("ai_messages", 0),
            "backtests": usage.get("backtests", 0),
        },
        "limits": {
            "ai_messages_per_day": limits["ai_messages_per_day"],
            "backtests_per_day": limits["backtests_per_day"],
            "ai_strategy_generator": limits["ai_strategy_generator"],
        },
    }
