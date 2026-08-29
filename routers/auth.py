from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)
from database import get_db
from dependencies import get_current_user
from models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    user_id: int
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUserResponse(BaseModel):
    user_id: int
    email: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Register a new user",
)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(
            request.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if (
        user is None
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get the current authenticated user",
)
def get_current_authenticated_user(
    current_user: User = Depends(get_current_user),
):
    return CurrentUserResponse(
        user_id=current_user.id,
        email=current_user.email,
    )