import os
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


_ALGORITHM = "HS256"
_COOKIE_NAME = "aitoolnity_session"


def _secret_key() -> str:
    secret = os.getenv("APP_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    return secret


def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires},
        _secret_key(),
        algorithm=_ALGORITHM,
    )


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[_ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.") from error
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    return user


def _fernet() -> Fernet:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="API key encryption is not configured. Set ENCRYPTION_KEY.",
        )
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise HTTPException(
            status_code=503,
            detail="ENCRYPTION_KEY must be a valid Fernet key.",
        ) from error


def encrypt_api_key(api_key: str) -> str:
    return _fernet().encrypt(api_key.encode("utf-8")).decode("ascii")


def decrypt_api_key(encrypted_api_key: str) -> str:
    try:
        return _fernet().decrypt(encrypted_api_key.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=500, detail="The saved API key could not be decrypted."
        ) from error


def session_cookie_name() -> str:
    return _COOKIE_NAME
