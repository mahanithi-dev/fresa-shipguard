from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import get_db
from app.entities import User
from app.services.security import decode_token, log_security_event

bearer = HTTPBearer(auto_error=True)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    client_ip = request.client.host if request.client else "unknown"
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        log_security_event("INVALID_JWT_TOKEN", f"JWT decode failure: {exc}", client_ip=client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    email = payload.get("sub")
    if not email:
        log_security_event("MALFORMED_JWT_PAYLOAD", "Missing sub claim in token", client_ip=client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        log_security_event("USER_NOT_FOUND", f"Token for non-existent email: {email}", client_ip=client_ip, user_identifier=email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(allowed_roles: list[str]) -> Callable:
    """Dependency factory enforcing server-side Role-Based Access Control (RBAC)."""
    def _role_checker(request: Request, user: User = Depends(get_current_user)) -> User:
        user_role = (user.role or "OPS_USER").upper()
        allowed_normalized = [r.upper() for r in allowed_roles]
        if user_role not in allowed_normalized:
            client_ip = request.client.host if request.client else "unknown"
            log_security_event(
                "UNAUTHORIZED_ROLE_ACCESS",
                f"User with role '{user.role}' attempted to access endpoint restricted to {allowed_roles}",
                client_ip=client_ip,
                user_identifier=user.email,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Insufficient privileges for this operation."
            )
        return user

    return _role_checker


require_admin = require_role(["ADMIN"])

