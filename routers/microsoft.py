from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from integrations.microsoft_graph import (
    create_microsoft_authorization_url,
    decode_oauth_state,
    exchange_code_for_token,
    get_microsoft_profile,
)
from models import MicrosoftConnection, User


router = APIRouter(
    prefix="/integrations/microsoft",
    tags=["Microsoft Integration"],
)


@router.get(
    "/connect",
    summary="Connect a Microsoft account",
)
def connect_microsoft(
    current_user: User = Depends(get_current_user),
):
    authorization_url = (
        create_microsoft_authorization_url(
            user_id=current_user.id,
        )
    )

    return {
        "authorization_url": authorization_url,
    }


@router.get(
    "/status",
    summary="Get Microsoft connection status",
)
def get_microsoft_connection_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connection = db.scalar(
        select(MicrosoftConnection).where(
            MicrosoftConnection.user_id
            == current_user.id
        )
    )

    if connection is None:
        return {
            "connected": False,
            "microsoft_connection": None,
        }

    return {
        "connected": True,
        "microsoft_connection": {
            "id": connection.id,
            "microsoft_user_id": (
                connection.microsoft_user_id
            ),
            "display_name": (
                connection.display_name
            ),
            "email": (
                connection.microsoft_email
            ),
            "connected_at": (
                connection.connected_at
            ),
        },
    }


@router.delete(
    "",
    summary="Disconnect Microsoft account",
)
def disconnect_microsoft(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connection = db.scalar(
        select(MicrosoftConnection).where(
            MicrosoftConnection.user_id
            == current_user.id
        )
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Microsoft account is not connected.",
        )

    db.delete(connection)
    db.commit()

    return {
        "status": "disconnected",
    }


@router.get(
    "/callback",
    summary="Handle Microsoft OAuth callback",
)
def microsoft_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    user_id = decode_oauth_state(state)

    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state.",
        )

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    try:
        token_result = exchange_code_for_token(
            code
        )

        profile = get_microsoft_profile(
            token_result["access_token"]
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Microsoft authentication failed: "
                f"{exc}"
            ),
        )

    microsoft_user_id = profile.get("id")

    microsoft_email = (
        profile.get("mail")
        or profile.get("userPrincipalName")
    )

    display_name = profile.get("displayName")

    if not microsoft_user_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Microsoft profile did not contain "
                "a user ID."
            ),
        )

    if not microsoft_email:
        raise HTTPException(
            status_code=400,
            detail=(
                "Microsoft profile did not contain "
                "an email address."
            ),
        )

    if not display_name:
        display_name = microsoft_email

    connection = db.scalar(
        select(MicrosoftConnection).where(
            MicrosoftConnection.user_id
            == user.id
        )
    )

    if connection is None:
        connection = MicrosoftConnection(
            user_id=user.id,
            microsoft_user_id=microsoft_user_id,
            microsoft_email=microsoft_email,
            display_name=display_name,
        )

        db.add(connection)

    else:
        connection.microsoft_user_id = (
            microsoft_user_id
        )
        connection.microsoft_email = (
            microsoft_email
        )
        connection.display_name = (
            display_name
        )

    db.commit()
    db.refresh(connection)

    return {
        "status": "connected",
        "local_user": user.email,
        "microsoft_connection": {
            "id": connection.id,
            "microsoft_user_id": (
                connection.microsoft_user_id
            ),
            "display_name": (
                connection.display_name
            ),
            "email": (
                connection.microsoft_email
            ),
            "connected_at": (
                connection.connected_at
            ),
        },
    }