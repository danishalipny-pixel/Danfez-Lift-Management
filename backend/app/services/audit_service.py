from typing import Optional
from sqlalchemy.orm import Session
from ..models.audit import AuditLog

def log_audit(
    db: Session,
    action: str,
    resource: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: str = "127.0.0.1"
):
    """Record an administrative or operational event in the audit log."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            user_email=user_email or "System/Guest",
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to write audit log: {e}")
