from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.technician import Technician
from ..models.maintenance import MaintenanceTicket
from ..models.user import User
from ..schemas.technician import (
    TechnicianCreate, TechnicianUpdate, TechnicianResponse
)
from ..auth.dependencies import get_current_user, require_admin
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/technicians", tags=["Technicians"])

@router.get("/", response_model=List[TechnicianResponse])
def get_technicians(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    techs = db.query(Technician).all()
    results = []
    for t in techs:
        active_count = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.assigned_technician_id == t.id,
            MaintenanceTicket.status.in_(["Open", "Assigned", "In Progress"])
        ).count()
        completed_count = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.assigned_technician_id == t.id,
            MaintenanceTicket.status.in_(["Resolved", "Closed"])
        ).count()

        results.append(TechnicianResponse(
            id=t.id,
            full_name=t.full_name,
            email=t.email,
            phone=t.phone,
            skills=t.skills,
            certification_level=t.certification_level,
            status=t.status,
            notes=t.notes,
            user_id=t.user_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
            active_tickets_count=active_count,
            completed_tickets_count=completed_count
        ))
    return results

@router.post("/", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
def create_technician(
    tech_in: TechnicianCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    existing = db.query(Technician).filter(Technician.email == tech_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A technician with this email already exists")

    tech = Technician(
        full_name=tech_in.full_name,
        email=tech_in.email,
        phone=tech_in.phone,
        skills=tech_in.skills,
        certification_level=tech_in.certification_level,
        status=tech_in.status,
        notes=tech_in.notes,
        user_id=tech_in.user_id
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)

    log_audit(
        db, action="TECHNICIAN_CREATED", resource=f"Technician:{tech.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Created technician profile for {tech.full_name}"
    )

    return TechnicianResponse(
        id=tech.id,
        full_name=tech.full_name,
        email=tech.email,
        phone=tech.phone,
        skills=tech.skills,
        certification_level=tech.certification_level,
        status=tech.status,
        notes=tech.notes,
        user_id=tech.user_id,
        created_at=tech.created_at,
        updated_at=tech.updated_at,
        active_tickets_count=0,
        completed_tickets_count=0
    )

@router.get("/{technician_id}", response_model=TechnicianResponse)
def get_technician(technician_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(Technician).filter(Technician.id == technician_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technician not found")

    active_count = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.assigned_technician_id == t.id,
        MaintenanceTicket.status.in_(["Open", "Assigned", "In Progress"])
    ).count()
    completed_count = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.assigned_technician_id == t.id,
        MaintenanceTicket.status.in_(["Resolved", "Closed"])
    ).count()

    return TechnicianResponse(
        id=t.id,
        full_name=t.full_name,
        email=t.email,
        phone=t.phone,
        skills=t.skills,
        certification_level=t.certification_level,
        status=t.status,
        notes=t.notes,
        user_id=t.user_id,
        created_at=t.created_at,
        updated_at=t.updated_at,
        active_tickets_count=active_count,
        completed_tickets_count=completed_count
    )

@router.put("/{technician_id}", response_model=TechnicianResponse)
def update_technician(
    technician_id: int,
    tech_update: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    t = db.query(Technician).filter(Technician.id == technician_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technician not found")

    if tech_update.full_name is not None:
        t.full_name = tech_update.full_name
    if tech_update.email is not None:
        t.email = tech_update.email
    if tech_update.phone is not None:
        t.phone = tech_update.phone
    if tech_update.skills is not None:
        t.skills = tech_update.skills
    if tech_update.certification_level is not None:
        t.certification_level = tech_update.certification_level
    if tech_update.status is not None:
        t.status = tech_update.status
    if tech_update.notes is not None:
        t.notes = tech_update.notes

    db.commit()
    db.refresh(t)

    log_audit(
        db, action="TECHNICIAN_UPDATED", resource=f"Technician:{t.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Updated technician profile {t.full_name}"
    )

    active_count = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.assigned_technician_id == t.id,
        MaintenanceTicket.status.in_(["Open", "Assigned", "In Progress"])
    ).count()
    completed_count = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.assigned_technician_id == t.id,
        MaintenanceTicket.status.in_(["Resolved", "Closed"])
    ).count()

    return TechnicianResponse(
        id=t.id,
        full_name=t.full_name,
        email=t.email,
        phone=t.phone,
        skills=t.skills,
        certification_level=t.certification_level,
        status=t.status,
        notes=t.notes,
        user_id=t.user_id,
        created_at=t.created_at,
        updated_at=t.updated_at,
        active_tickets_count=active_count,
        completed_tickets_count=completed_count
    )

@router.delete("/{technician_id}")
def delete_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    t = db.query(Technician).filter(Technician.id == technician_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Technician not found")

    # Safe toggle to Inactive
    t.status = "Inactive"
    db.commit()

    log_audit(
        db, action="TECHNICIAN_DEACTIVATED", resource=f"Technician:{t.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Deactivated technician {t.full_name}"
    )
    return {"message": f"Technician {t.full_name} marked as Inactive"}
