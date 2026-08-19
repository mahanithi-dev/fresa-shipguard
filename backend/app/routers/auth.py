from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.entities import User
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.services.rate_limiter import check_auth_rate_limit
from app.services.security import create_access_token, hash_password, log_security_event, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(check_auth_rate_limit)])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    normalized_email = payload.email.strip().lower()

    user = db.query(User).filter(User.email.ilike(normalized_email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        log_security_event("LOGIN_FAILED", f"Failed login attempt for {normalized_email}", client_ip=client_ip, user_identifier=normalized_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    log_security_event("LOGIN_SUCCESS", f"Successful login for {user.email}", client_ip=client_ip, user_identifier=user.email)
    return TokenResponse(access_token=create_access_token(user.email, role=user.role or "OPS_USER"))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_auth_rate_limit)])
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    normalized_email = payload.email.strip().lower()

    existing = db.query(User).filter(User.email.ilike(normalized_email)).first()
    if existing:
        log_security_event("REGISTER_DUPLICATE", f"Registration attempt for existing email {normalized_email}", client_ip=client_ip, user_identifier=normalized_email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")

    # Security Fix: Prevent privilege escalation. Public self-registration always assigns OPS_USER role.
    hashed = hash_password(payload.password)
    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hashed,
        role="OPS_USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event("USER_REGISTERED", f"New user registered: {user.email}", client_ip=client_ip, user_identifier=user.email)
    return TokenResponse(access_token=create_access_token(user.email, role=user.role))

