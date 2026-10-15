from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.user import User
from ..models.auth_token import PasswordResetToken, RevokedToken
from ..schemas.auth import (
    LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest,
    VerifyEmailRequest, GoogleAuthRequest, ProfileUpdateRequest,
    Token, PasswordChangeRequest
)
from ..schemas.user import UserResponse
from ..auth.security import verify_password, hash_password, create_access_token, decode_access_token
from ..auth.dependencies import get_current_user, security_bearer
from ..services.audit_service import log_audit
from ..services.email_service import email_service
from ..services.oauth_service import google_oauth

router = APIRouter(prefix="/api/auth", tags=["Authentication & Accounts"])

def now_utc():
    return datetime.now(timezone.utc)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user account with application-specific credentials."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in or reset your password."
        )

    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    # Allowed public self-registration roles default to 'viewer'
    assigned_role = req.role if req.role in ("viewer", "technician") else "viewer"

    # Generate verification token
    verification_token = uuid.uuid4().hex
    token_expires = now_utc() + timedelta(days=2)

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=assigned_role,
        phone=req.phone,
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Dispatch verification email
    email_service.send_verification_email(user.email, user.full_name, verification_token)

    log_audit(
        db, action="USER_REGISTERED", resource=f"User:{user.id}",
        user_id=user.id, user_email=user.email,
        details=f"New user self-registered with role '{assigned_role}'",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return user

@router.post("/login", response_model=Token)
def login(request_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with email and password. Supports Remember-Me option."""
    user = db.query(User).filter(User.email == request_data.email).first()
    if not user or not verify_password(request_data.password, user.hashed_password):
        log_audit(
            db, action="LOGIN_FAILED", resource="Auth",
            user_email=request_data.email, details="Invalid credentials attempted",
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated. Please contact an administrator."
        )

    # Create access token with jti and remember_me flag
    access_token, expire_dt = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        remember_me=bool(request_data.remember_me)
    )

    log_audit(
        db, action="LOGIN_SUCCESS", resource=f"User:{user.id}",
        user_id=user.id, user_email=user.email,
        details=f"Login successful (Remember-Me: {request_data.remember_me})",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        user_id=user.id,
        is_verified=user.is_verified,
        expires_at=expire_dt.isoformat()
    )

@router.post("/logout")
def logout(
    request: Request,
    credentials = Depends(security_bearer),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke current JWT token session upon logout."""
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else now_utc() + timedelta(days=1)
                revoked = RevokedToken(
                    token_jti=jti,
                    user_id=current_user.id,
                    expires_at=exp_dt
                )
                db.add(revoked)
                db.commit()

    log_audit(
        db, action="USER_LOGOUT", resource=f"User:{current_user.id}",
        user_id=current_user.id, user_email=current_user.email,
        details="User logged out; active session token revoked.",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return {"message": "Session terminated and revoked successfully."}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Initiate password recovery by issuing a single-use expiring reset token."""
    user = db.query(User).filter(User.email == req.email).first()
    
    # Anti-enumeration: return success message even if account is not found
    dev_info = None
    if user and user.is_active:
        # Invalidate any previous unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

        # Generate single-use secure reset token
        token_str = uuid.uuid4().hex + uuid.uuid4().hex
        expires_at = now_utc() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
        
        reset_entry = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
            is_used=False
        )
        db.add(reset_entry)
        db.commit()

        email_result = email_service.send_password_reset_email(user.email, user.full_name, token_str)
        dev_info = email_result["reset_url"]

        log_audit(
            db, action="PASSWORD_RESET_REQUESTED", resource=f"User:{user.id}",
            user_id=user.id, user_email=user.email,
            details="Password recovery token generated and dispatched.",
            ip_address=request.client.host if request.client else "127.0.0.1"
        )

    return {
        "message": "If an account exists with this email address, password recovery instructions have been sent.",
        "reset_link": dev_info if settings.DEBUG else None,
        "reset_token": token_str if (settings.DEBUG and user) else None
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Validate single-use reset token and update password."""
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token
    ).first()

    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token."
        )

    if reset_entry.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used. Please request a new link."
        )

    # Check expiration (compare with UTC aware)
    now = now_utc()
    expires_at = reset_entry.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has expired. Please request a fresh reset link."
        )

    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long."
        )

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Associated user account not found.")

    # Update password and consume token
    user.hashed_password = hash_password(req.new_password)
    user.is_verified = True # Resetting via email proves email ownership
    reset_entry.is_used = True
    db.commit()

    log_audit(
        db, action="PASSWORD_RESET_COMPLETED", resource=f"User:{user.id}",
        user_id=user.id, user_email=user.email,
        details="Password successfully updated via reset token.",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return {"message": "Password updated successfully. You may now log in with your new password."}

@router.get("/verify-email")
def verify_email(token: str = Query(..., description="Email verification token"), db: Session = Depends(get_db)):
    """Verify user account email address."""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token."
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    log_audit(
        db, action="EMAIL_VERIFIED", resource=f"User:{user.id}",
        user_id=user.id, user_email=user.email,
        details="User verified their email address successfully."
    )

    return {"message": "Email address verified successfully! Your account is fully active.", "email": user.email}

@router.post("/resend-verification")
def resend_verification(email: str = Query(..., description="User email"), db: Session = Depends(get_db)):
    """Resend email verification token."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If an account exists, a verification link has been sent."}

    if user.is_verified:
        return {"message": "This email address is already verified."}

    token = uuid.uuid4().hex
    user.verification_token = token
    user.verification_token_expires = now_utc() + timedelta(days=2)
    db.commit()

    email_service.send_verification_email(user.email, user.full_name, token)
    return {"message": "A new verification email has been sent."}

@router.post("/google", response_model=Token)
async def google_auth(req: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """Sign in or register using Google OpenID Connect (OAuth 2.0)."""
    token_str = req.credential or req.code
    google_data = await google_oauth.verify_google_id_token(token_str)
    
    email = google_data["email"]
    name = google_data.get("name", "Google User")
    google_id = google_data.get("google_id")
    avatar = google_data.get("avatar_url")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create new user via Google
        user = User(
            email=email,
            hashed_password=hash_password(uuid.uuid4().hex + uuid.uuid4().hex),
            full_name=name,
            role="viewer",
            google_id=google_id,
            avatar_url=avatar,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log_audit(
            db, action="GOOGLE_REGISTER", resource=f"User:{user.id}",
            user_id=user.id, user_email=user.email,
            details="New account created via Google Sign-In",
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
    else:
        # Link Google ID and avatar if not present
        if not user.google_id:
            user.google_id = google_id
        if not user.avatar_url and avatar:
            user.avatar_url = avatar
        user.is_verified = True
        db.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator."
        )

    access_token, expire_dt = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        remember_me=True
    )

    log_audit(
        db, action="GOOGLE_LOGIN", resource=f"User:{user.id}",
        user_id=user.id, user_email=user.email,
        details="User authenticated via Google Sign-In",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        user_id=user.id,
        is_verified=user.is_verified,
        expires_at=expire_dt.isoformat()
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current user profile."""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile details for the authenticated user."""
    if req.full_name is not None and req.full_name.strip():
        current_user.full_name = req.full_name.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip()

    db.commit()
    db.refresh(current_user)

    log_audit(
        db, action="PROFILE_UPDATED", resource=f"User:{current_user.id}",
        user_id=current_user.id, user_email=current_user.email,
        details="User updated personal profile details."
    )
    return current_user

@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    
    log_audit(
        db, action="PASSWORD_CHANGE", resource=f"User:{current_user.id}",
        user_id=current_user.id, user_email=current_user.email,
        details="User updated their account password"
    )
    return {"message": "Password updated successfully"}
