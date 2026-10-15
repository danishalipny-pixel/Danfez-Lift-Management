from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="viewer") # admin, technician, viewer
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    google_id = Column(String(255), nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    technician_profile = relationship("Technician", back_populates="user", uselist=False)
    created_tickets = relationship("MaintenanceTicket", back_populates="creator", foreign_keys="MaintenanceTicket.created_by_id")
    audit_logs = relationship("AuditLog", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    revoked_sessions = relationship("RevokedToken", back_populates="user", cascade="all, delete-orphan")
