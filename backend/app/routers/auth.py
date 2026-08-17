from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..email_service import send_password_reset_email
from ..models import AuditLog, PasswordResetToken, RiskSettings, User
from ..schemas import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, ResetPasswordRequest,
    SignupRequest, TokenResponse, UserOut,
)
from ..security import (
    create_access_token, generate_reset_token, hash_password, hash_token, verify_password,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def log_action(db: Session, user_id: str, action: str, detail: str = "", level: str = "info"):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail, level=level))
    db.commit()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Every user gets default risk settings on signup
    db.add(RiskSettings(user_id=user.id))
    db.commit()

    log_action(db, user.id, "signup", f"New account created: {user.email}")
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(subject=user.id, extra={"role": user.role.value})
    log_action(db, user.id, "login", f"Login from email: {user.email}")
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 525600)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    # Always return the same response whether or not the email exists (prevents user enumeration)
    if user:
        raw_token, hashed = generate_reset_token()
        expires = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
        db.add(PasswordResetToken(user_id=user.id, token_hash=hashed, expires_at=expires))
        db.commit()

        reset_link = f"{settings.FRONTEND_URL}/reset-password.html?token={raw_token}"
        send_password_reset_email(user.email, reset_link)
        log_action(db, user.id, "forgot_password_requested")

    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    hashed = hash_token(payload.token)
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hashed, PasswordResetToken.used == False)  # noqa: E712
        .first()
    )
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired.")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")

    user.hashed_password = hash_password(payload.new_password)
    record.used = True
    db.commit()
    log_action(db, user.id, "password_reset")
    return {"message": "Password has been reset successfully. You can now log in."}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    log_action(db, current_user.id, "password_changed")
    return {"message": "Password changed successfully."}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # JWT is stateless; logout is enforced client-side by discarding the token.
    # We still log it server-side for audit purposes.
    log_action(db, current_user.id, "logout")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
