import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.entities import User
from app.models.schemas import GoogleAuthRequest, LoginRequest, RegisterRequest, TokenResponse
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


@router.post("/google", response_model=TokenResponse, dependencies=[Depends(check_auth_rate_limit)])
def google_auth(payload: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    settings = get_settings()

    try:
        # Verify the Google ID token server-side (signature, audience, issuer, expiry)
        audience = settings.google_client_id if settings.google_client_id else None

        id_info = id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            audience=audience
        )

        # Verify issuer
        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            log_security_event("GOOGLE_AUTH_FAILED", "Invalid Google ID token issuer", client_ip=client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token issuer")

        # Verify email presence and Google email_verified flag
        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account does not provide an email address")

        email_verified = id_info.get("email_verified", False)
        if not email_verified:
            log_security_event("GOOGLE_AUTH_FAILED", f"Unverified Google email {email}", client_ip=client_ip, user_identifier=email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email address has not been verified by Google")

        normalized_email = email.strip().lower()
        name = id_info.get("name") or id_info.get("given_name") or normalized_email.split("@")[0]

        # Match or create user record
        user = db.query(User).filter(User.email.ilike(normalized_email)).first()
        if user is None:
            # Create new user for Google Sign-in with random unguessable password hash
            random_pw = secrets.token_urlsafe(32)
            user = User(
                name=name.strip(),
                email=normalized_email,
                password_hash=hash_password(random_pw),
                role="OPS_USER",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log_security_event("GOOGLE_USER_REGISTERED", f"New user created via Google Sign-In: {user.email}", client_ip=client_ip, user_identifier=user.email)
        else:
            log_security_event("GOOGLE_LOGIN_SUCCESS", f"Existing user signed in via Google: {user.email}", client_ip=client_ip, user_identifier=user.email)

        # Issue ShipGuard JWT access token
        return TokenResponse(access_token=create_access_token(user.email, role=user.role or "OPS_USER"))

    except HTTPException:
        raise
    except ValueError as e:
        log_security_event("GOOGLE_AUTH_INVALID_TOKEN", f"Google token verification failed: {e}", client_ip=client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Google authentication failed: {str(e)}")
    except Exception as e:
        log_security_event("GOOGLE_AUTH_ERROR", f"Unexpected Google auth error: {e}", client_ip=client_ip)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during Google authentication. Please try again.")

