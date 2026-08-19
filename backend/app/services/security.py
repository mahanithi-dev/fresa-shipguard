import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import HTTPException, status
from jose import jwt

from app.config import get_settings

logger = logging.getLogger("shipguard.security")


def validate_password_strength(password: str) -> None:
    """Enforces minimum password security policy."""
    settings = get_settings()
    min_len = getattr(settings, "min_password_length", 8)
    if not password or len(password) < min_len:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Password must be at least {min_len} characters long."
        )
    if len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password exceeds maximum length of 128 characters."
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, role: str = "OPS_USER") -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": subject,
        "role": role,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])


def sanitize_csv_cell(value: Any) -> str:
    """Neutralizes CSV / Formula Injection (CWE-1236).

    If the text starts with dangerous formula trigger characters (=, +, -, @, \\t, \\r),
    preprend a single quote (') to force spreadsheet software (Excel, Calc) to treat it as text.
    """
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def log_security_event(event_type: str, details: str, client_ip: str = "unknown", user_identifier: str = "anonymous") -> None:
    """Structured security audit log avoiding sensitive credential/token disclosure."""
    logger.warning(
        "SECURITY_AUDIT: type=%s | user=%s | ip=%s | details=%s",
        event_type,
        user_identifier,
        client_ip,
        details,
    )

