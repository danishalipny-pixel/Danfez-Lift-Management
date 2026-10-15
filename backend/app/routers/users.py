from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, UserResponse
from ..auth.dependencies import require_admin
from ..auth.security import hash_password
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/users", tags=["User Management"])

@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.id.asc()).all()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
    
    if user_in.role not in ("admin", "technician", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: 'admin', 'technician', 'viewer'"
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        phone=user_in.phone,
        is_active=user_in.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db, action="USER_CREATED", resource=f"User:{user.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Created user {user.email} with role {user.role}"
    )
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        if user_update.role not in ("admin", "technician", "viewer"):
            raise HTTPException(status_code=400, detail="Invalid role specified")
        user.role = user_update.role
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.is_active is not None:
        # Prevent admin deactivating their own account
        if user.id == current_admin.id and not user_update.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own administrator account")
        user.is_active = user_update.is_active
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)

    db.commit()
    db.refresh(user)

    log_audit(
        db, action="USER_UPDATED", resource=f"User:{user.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Updated details for user {user.email}"
    )
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own administrator account")

    # Safe deactivation
    user.is_active = False
    db.commit()

    log_audit(
        db, action="USER_DEACTIVATED", resource=f"User:{user.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Deactivated user account {user.email}"
    )
    return {"message": "User deactivated successfully"}
