from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
import bcrypt
import jwt
from ..config import settings

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    remember_me: bool = False
) -> Tuple[str, datetime]:
    """
    Create a signed JWT access token with unique JTI.
    Supports Remember-Me for longer multi-device sessions.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    elif remember_me:
        expire = now + timedelta(days=settings.REMEMBER_ME_EXPIRE_DAYS)
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Assign unique JWT identifier (jti) for session tracking and revocation
    jti = uuid.uuid4().hex
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "remember_me": remember_me
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
