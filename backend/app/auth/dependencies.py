from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.auth_token import RevokedToken
from .security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or not credentials.credentials:
        raise credentials_exception
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    # Check if this token was revoked upon logout
    jti = payload.get("jti")
    if jti:
        revoked = db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first()
        if revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This session has been revoked upon logout. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    email: str = payload.get("sub")
    if not email:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact an administrator."
        )
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action"
        )
    return current_user

def require_technician_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "technician"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician or Admin privileges required for this action"
        )
    return current_user

def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if not payload:
            return None
        jti = payload.get("jti")
        if jti:
            revoked = db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first()
            if revoked:
                return None
        email = payload.get("sub")
        if not email:
            return None
        return db.query(User).filter(User.email == email, User.is_active == True).first()
    except Exception:
        return None
