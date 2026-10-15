from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.setting import SystemSetting
from ..models.audit import AuditLog
from ..models.user import User
from ..schemas.setting import SettingResponse, SystemConfigUpdate
from ..schemas.audit import AuditLogResponse
from ..auth.dependencies import get_current_user, require_admin
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/settings", tags=["System Settings & Audit"])

@router.get("/", response_model=List[SettingResponse])
def get_all_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SystemSetting).all()

@router.put("/batch")
def update_batch_settings(
    config: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    updates = {}
    if config.building_name is not None:
        updates["building_name"] = config.building_name
    if config.default_floors is not None:
        updates["default_floors"] = str(config.default_floors)
    if config.simulation_speed is not None:
        updates["simulation_speed"] = str(config.simulation_speed)
    if config.emergency_phone is not None:
        updates["emergency_phone"] = config.emergency_phone
    if config.maintenance_interval_days is not None:
        updates["maintenance_interval_days"] = str(config.maintenance_interval_days)
    if config.email_notifications_enabled is not None:
        updates["email_notifications_enabled"] = "true" if config.email_notifications_enabled else "false"

    for key, val in updates.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = val
        else:
            db.add(SystemSetting(key=key, value=val))

    db.commit()

    log_audit(
        db, action="SETTINGS_UPDATED", resource="SystemConfig",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Admin updated system settings: {list(updates.keys())}"
    )

    return {"message": "Settings updated successfully", "updated_keys": list(updates.keys())}

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
