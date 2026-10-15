from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from ..database import get_db
from ..models.fault import FaultAlert
from ..models.elevator import Elevator
from ..models.technician import Technician
from ..models.user import User
from ..schemas.fault import (
    FaultAlertCreate, FaultAlertAcknowledge, FaultAlertResolve, FaultAlertResponse
)
from ..auth.dependencies import get_current_user, get_optional_current_user, require_technician_or_admin
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/faults", tags=["Fault & Alert Center"])

@router.get("/", response_model=List[FaultAlertResponse])
def get_faults(
    severity: Optional[str] = Query(None),
    is_acknowledged: Optional[bool] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    elevator_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = db.query(FaultAlert)

    if severity and severity != "All":
        query = query.filter(FaultAlert.severity == severity)
    if is_acknowledged is not None:
        query = query.filter(FaultAlert.is_acknowledged == is_acknowledged)
    if is_resolved is not None:
        query = query.filter(FaultAlert.is_resolved == is_resolved)
    if elevator_id:
        query = query.filter(FaultAlert.elevator_id == elevator_id)
    if search:
        search_filter = or_(
            FaultAlert.fault_code.ilike(f"%{search}%"),
            FaultAlert.description.ilike(f"%{search}%"),
            FaultAlert.category.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    query = query.order_by(desc(FaultAlert.created_at))
    faults = query.offset(skip).limit(limit).all()

    results = []
    for f in faults:
        results.append(FaultAlertResponse(
            id=f.id,
            fault_code=f.fault_code,
            elevator_id=f.elevator_id,
            severity=f.severity,
            category=f.category,
            description=f.description,
            assigned_technician_id=f.assigned_technician_id,
            is_acknowledged=f.is_acknowledged,
            acknowledged_at=f.acknowledged_at,
            acknowledged_by_id=f.acknowledged_by_id,
            is_resolved=f.is_resolved,
            resolution_notes=f.resolution_notes,
            resolved_at=f.resolved_at,
            resolved_by_id=f.resolved_by_id,
            created_at=f.created_at,
            elevator_name=f.elevator.name if f.elevator else None,
            elevator_code=f.elevator.code if f.elevator else None,
            technician_name=f.assigned_technician.full_name if f.assigned_technician else "Unassigned"
        ))
    return results

@router.post("/", response_model=FaultAlertResponse, status_code=status.HTTP_201_CREATED)
def create_fault(
    fault_in: FaultAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_admin)
):
    elevator = db.query(Elevator).filter(Elevator.id == fault_in.elevator_id).first()
    if not elevator:
        raise HTTPException(status_code=400, detail="Referenced elevator does not exist")

    import uuid
    fault_code = f"FLT-2026-{uuid.uuid4().hex[:5].upper()}"

    fault = FaultAlert(
        fault_code=fault_code,
        elevator_id=fault_in.elevator_id,
        severity=fault_in.severity,
        category=fault_in.category,
        description=fault_in.description,
        assigned_technician_id=fault_in.assigned_technician_id,
        is_acknowledged=False,
        is_resolved=False
    )
    db.add(fault)
    if fault_in.severity in ("High", "Critical"):
        elevator.status = "fault"

    db.commit()
    db.refresh(fault)

    log_audit(
        db, action="FAULT_LOGGED", resource=f"Fault:{fault.fault_code}",
        user_id=current_user.id, user_email=current_user.email,
        details=f"Fault logged on {elevator.code} ({fault.severity}): {fault.description[:50]}"
    )

    return FaultAlertResponse(
        id=fault.id,
        fault_code=fault.fault_code,
        elevator_id=fault.elevator_id,
        severity=fault.severity,
        category=fault.category,
        description=fault.description,
        assigned_technician_id=fault.assigned_technician_id,
        is_acknowledged=fault.is_acknowledged,
        acknowledged_at=fault.acknowledged_at,
        acknowledged_by_id=fault.acknowledged_by_id,
        is_resolved=fault.is_resolved,
        resolution_notes=fault.resolution_notes,
        resolved_at=fault.resolved_at,
        resolved_by_id=fault.resolved_by_id,
        created_at=fault.created_at,
        elevator_name=elevator.name,
        elevator_code=elevator.code,
        technician_name=fault.assigned_technician.full_name if fault.assigned_technician else "Unassigned"
    )

@router.post("/{fault_id}/acknowledge", response_model=FaultAlertResponse)
def acknowledge_fault(
    fault_id: int,
    ack_data: Optional[FaultAlertAcknowledge] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_admin)
):
    fault = db.query(FaultAlert).filter(FaultAlert.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault alert not found")

    fault.is_acknowledged = True
    fault.acknowledged_at = datetime.utcnow()
    fault.acknowledged_by_id = current_user.id

    if ack_data and ack_data.assigned_technician_id:
        fault.assigned_technician_id = ack_data.assigned_technician_id

    db.commit()
    db.refresh(fault)

    log_audit(
        db, action="FAULT_ACKNOWLEDGED", resource=f"Fault:{fault.fault_code}",
        user_id=current_user.id, user_email=current_user.email,
        details=f"Fault {fault.fault_code} acknowledged by {current_user.email}"
    )

    return FaultAlertResponse(
        id=fault.id,
        fault_code=fault.fault_code,
        elevator_id=fault.elevator_id,
        severity=fault.severity,
        category=fault.category,
        description=fault.description,
        assigned_technician_id=fault.assigned_technician_id,
        is_acknowledged=fault.is_acknowledged,
        acknowledged_at=fault.acknowledged_at,
        acknowledged_by_id=fault.acknowledged_by_id,
        is_resolved=fault.is_resolved,
        resolution_notes=fault.resolution_notes,
        resolved_at=fault.resolved_at,
        resolved_by_id=fault.resolved_by_id,
        created_at=fault.created_at,
        elevator_name=fault.elevator.name if fault.elevator else None,
        elevator_code=fault.elevator.code if fault.elevator else None,
        technician_name=fault.assigned_technician.full_name if fault.assigned_technician else "Unassigned"
    )

@router.post("/{fault_id}/resolve", response_model=FaultAlertResponse)
def resolve_fault(
    fault_id: int,
    res_data: FaultAlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_admin)
):
    fault = db.query(FaultAlert).filter(FaultAlert.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault alert not found")

    fault.is_resolved = True
    fault.resolved_at = datetime.utcnow()
    fault.resolved_by_id = current_user.id
    fault.resolution_notes = res_data.resolution_notes
    if not fault.is_acknowledged:
        fault.is_acknowledged = True
        fault.acknowledged_at = datetime.utcnow()
        fault.acknowledged_by_id = current_user.id

    # If no other unresolved faults for this elevator, restore operational status
    other_faults = db.query(FaultAlert).filter(
        FaultAlert.elevator_id == fault.elevator_id,
        FaultAlert.id != fault.id,
        FaultAlert.is_resolved == False
    ).count()

    if other_faults == 0 and fault.elevator:
        fault.elevator.status = "operational"
        fault.elevator.emergency_stopped = False

    db.commit()
    db.refresh(fault)

    log_audit(
        db, action="FAULT_RESOLVED", resource=f"Fault:{fault.fault_code}",
        user_id=current_user.id, user_email=current_user.email,
        details=f"Fault {fault.fault_code} resolved: {res_data.resolution_notes[:50]}"
    )

    return FaultAlertResponse(
        id=fault.id,
        fault_code=fault.fault_code,
        elevator_id=fault.elevator_id,
        severity=fault.severity,
        category=fault.category,
        description=fault.description,
        assigned_technician_id=fault.assigned_technician_id,
        is_acknowledged=fault.is_acknowledged,
        acknowledged_at=fault.acknowledged_at,
        acknowledged_by_id=fault.acknowledged_by_id,
        is_resolved=fault.is_resolved,
        resolution_notes=fault.resolution_notes,
        resolved_at=fault.resolved_at,
        resolved_by_id=fault.resolved_by_id,
        created_at=fault.created_at,
        elevator_name=fault.elevator.name if fault.elevator else None,
        elevator_code=fault.elevator.code if fault.elevator else None,
        technician_name=fault.assigned_technician.full_name if fault.assigned_technician else "Unassigned"
    )
