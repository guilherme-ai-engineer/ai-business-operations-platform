from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth_service import decode_access_token
from database import get_db
from models import User


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    payload = decode_access_token(
        token
    )

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    try:
        user_id = int(user_id)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required.",
        )

    return current_user