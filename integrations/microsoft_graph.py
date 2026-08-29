import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from jose import JWTError, jwt
from msal import ConfidentialClientApplication


load_dotenv()


MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
MICROSOFT_TENANT = os.getenv(
    "MICROSOFT_TENANT",
    "common",
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)


if not MICROSOFT_CLIENT_ID:
    raise RuntimeError(
        "MICROSOFT_CLIENT_ID is missing from .env"
    )

if not MICROSOFT_CLIENT_SECRET:
    raise RuntimeError(
        "MICROSOFT_CLIENT_SECRET is missing from .env"
    )

if not MICROSOFT_REDIRECT_URI:
    raise RuntimeError(
        "MICROSOFT_REDIRECT_URI is missing from .env"
    )

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing from .env"
    )


MICROSOFT_AUTHORITY = (
    "https://login.microsoftonline.com/"
    f"{MICROSOFT_TENANT}"
)

MICROSOFT_SCOPES = [
    "User.Read",
]

MICROSOFT_GRAPH_ME_URL = (
    "https://graph.microsoft.com/v1.0/me"
)


def get_microsoft_client() -> ConfidentialClientApplication:
    return ConfidentialClientApplication(
        client_id=MICROSOFT_CLIENT_ID,
        authority=MICROSOFT_AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )


def create_oauth_state(
    user_id: int,
) -> str:
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )

    payload = {
        "sub": str(user_id),
        "purpose": "microsoft_oauth",
        "nonce": str(uuid4()),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_oauth_state(
    state: str,
) -> int | None:
    try:
        payload = jwt.decode(
            state,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

    except JWTError:
        return None

    if payload.get("purpose") != "microsoft_oauth":
        return None

    user_id = payload.get("sub")

    if user_id is None:
        return None

    try:
        return int(user_id)

    except (TypeError, ValueError):
        return None


def create_microsoft_authorization_url(
    user_id: int,
) -> str:
    state = create_oauth_state(
        user_id=user_id,
    )

    client = get_microsoft_client()

    return client.get_authorization_request_url(
        scopes=MICROSOFT_SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
        state=state,
        prompt="select_account",
    )


def exchange_code_for_token(
    code: str,
) -> dict:
    client = get_microsoft_client()

    result = client.acquire_token_by_authorization_code(
        code=code,
        scopes=MICROSOFT_SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )

    if "access_token" not in result:
        error_description = result.get(
            "error_description",
            "Microsoft token exchange failed.",
        )

        raise RuntimeError(
            error_description
        )

    return result


def get_microsoft_profile(
    access_token: str,
) -> dict:
    response = httpx.get(
        MICROSOFT_GRAPH_ME_URL,
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        timeout=15.0,
    )

    response.raise_for_status()

    return response.json()