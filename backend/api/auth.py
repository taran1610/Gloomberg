from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.auth import (
    register_user,
    authenticate_user,
    create_token,
    require_auth,
    user_public,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if len(body.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    try:
        user = register_user(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    token = create_token(user["id"])
    return {"token": token, "user": user_public(user)}


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    user = authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"])
    return {"token": token, "user": user_public(user)}


@router.get("/me")
async def me(user: dict = Depends(require_auth)):
    return user_public(user)
