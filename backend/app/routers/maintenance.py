from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from ..database import get_db
from ..models.maintenance import MaintenanceTicket
from ..models.elevator import Elevator
from ..models.technician import Technician
from ..models.user import User
from ..schemas.maintenance import (
    MaintenanceTicketCreate, MaintenanceTicketUpdate, MaintenanceTicketResponse
)
from ..auth.dependencies import get_current_user, get_optional_current_user, require_technician_or_admin, require_admin
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance Tickets"])

@router.get("/", response_model=List[MaintenanceTicketResponse])
def get_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    elevator_id: Optional[int] = Query(None),
    technician_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    order: Optional[str] = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = db.query(MaintenanceTicket)

    if status and status != "All":
        query = query.filter(MaintenanceTicket.status == status)
    if priority and priority != "All":
        query = query.filter(MaintenanceTicket.priority == priority)
    if elevator_id:
        query = query.filter(MaintenanceTicket.elevator_id == elevator_id)
    if technician_id:
        query = query.filter(MaintenanceTicket.assigned_technician_id == technician_id)
    if search:
        search_filter = or_(
            MaintenanceTicket.ticket_number.ilike(f"%{search}%"),
            MaintenanceTicket.description.ilike(f"%{search}%"),
            MaintenanceTicket.category.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Sorting
    sort_attr = getattr(MaintenanceTicket, sort_by, MaintenanceTicket.created_at)
    if order == "asc":
        query = query.order_by(asc(sort_attr))
    else:
        query = query.order_by(desc(sort_attr))

    tickets = query.offset(skip).limit(limit).all()

    results = []
    for t in tickets:
        results.append(MaintenanceTicketResponse(
            id=t.id,
            ticket_number=t.ticket_number,
            elevator_id=t.elevator_id,
            category=t.category,
            priority=t.priority,
            status=t.status,
            description=t.description,
            assigned_technician_id=t.assigned_technician_id,
            created_by_id=t.created_by_id,
            scheduled_date=t.scheduled_date,
            completion_date=t.completion_date,
            resolution_notes=t.resolution_notes,
            created_at=t.created_at,
            updated_at=t.updated_at,
            elevator_name=t.elevator.name if t.elevator else None,
            elevator_code=t.elevator.code if t.elevator else None,
            technician_name=t.assigned_technician.full_name if t.assigned_technician else "Unassigned"
        ))
    return results

@router.post("/", response_model=MaintenanceTicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: MaintenanceTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_admin)
):
    elevator = db.query(Elevator).filter(Elevator.id == ticket_in.elevator_id).first()
    if not elevator:
        raise HTTPException(status_code=400, detail="Referenced elevator does not exist")

    # Generate sequential unique ticket number
    count = db.query(MaintenanceTicket).count() + 1
    ticket_number = f"MNT-2026-{count:03d}"

    ticket = MaintenanceTicket(
        ticket_number=ticket_number,
        elevator_id=ticket_in.elevator_id,
        category=ticket_in.category,
        priority=ticket_in.priority,
        status=ticket_in.status if ticket_in.assigned_technician_id else "Open",
        description=ticket_in.description,
        assigned_technician_id=ticket_in.assigned_technician_id,
        scheduled_date=ticket_in.scheduled_date,
        created_by_id=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    log_audit(
        db, action="TICKET_CREATED", resource=f"Ticket:{ticket.ticket_number}",
        user_id=current_user.id, user_email=current_user.email,
        details=f"Created ticket {ticket.ticket_number} for elevator {elevator.code}"
    )

    return MaintenanceTicketResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        elevator_id=ticket.elevator_id,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        description=ticket.description,
        assigned_technician_id=ticket.assigned_technician_id,
        created_by_id=ticket.created_by_id,
        scheduled_date=ticket.scheduled_date,
        completion_date=ticket.completion_date,
        resolution_notes=ticket.resolution_notes,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        elevator_name=elevator.name,
        elevator_code=elevator.code,
        technician_name=ticket.assigned_technician.full_name if ticket.assigned_technician else "Unassigned"
    )

@router.get("/{ticket_id}", response_model=MaintenanceTicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")

    return MaintenanceTicketResponse(
        id=t.id,
        ticket_number=t.ticket_number,
        elevator_id=t.elevator_id,
        category=t.category,
        priority=t.priority,
        status=t.status,
        description=t.description,
        assigned_technician_id=t.assigned_technician_id,
        created_by_id=t.created_by_id,
        scheduled_date=t.scheduled_date,
        completion_date=t.completion_date,
        resolution_notes=t.resolution_notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
        elevator_name=t.elevator.name if t.elevator else None,
        elevator_code=t.elevator.code if t.elevator else None,
        technician_name=t.assigned_technician.full_name if t.assigned_technician else "Unassigned"
    )

@router.put("/{ticket_id}", response_model=MaintenanceTicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: MaintenanceTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_admin)
):
    t = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")

    if ticket_update.category is not None:
        t.category = ticket_update.category
    if ticket_update.priority is not None:
        t.priority = ticket_update.priority
    if ticket_update.description is not None:
        t.description = ticket_update.description
    if ticket_update.assigned_technician_id is not None:
        t.assigned_technician_id = ticket_update.assigned_technician_id
        if t.status == "Open":
            t.status = "Assigned"
    if ticket_update.scheduled_date is not None:
        t.scheduled_date = ticket_update.scheduled_date
    if ticket_update.resolution_notes is not None:
        t.resolution_notes = ticket_update.resolution_notes
    if ticket_update.status is not None:
        t.status = ticket_update.status
        if ticket_update.status in ("Resolved", "Closed") and not t.completion_date:
            t.completion_date = datetime.utcnow()
    if ticket_update.completion_date is not None:
        t.completion_date = ticket_update.completion_date

    db.commit()
    db.refresh(t)

    log_audit(
        db, action="TICKET_UPDATED", resource=f"Ticket:{t.ticket_number}",
        user_id=current_user.id, user_email=current_user.email,
        details=f"Updated status to {t.status} for ticket {t.ticket_number}"
    )

    return MaintenanceTicketResponse(
        id=t.id,
        ticket_number=t.ticket_number,
        elevator_id=t.elevator_id,
        category=t.category,
        priority=t.priority,
        status=t.status,
        description=t.description,
        assigned_technician_id=t.assigned_technician_id,
        created_by_id=t.created_by_id,
        scheduled_date=t.scheduled_date,
        completion_date=t.completion_date,
        resolution_notes=t.resolution_notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
        elevator_name=t.elevator.name if t.elevator else None,
        elevator_code=t.elevator.code if t.elevator else None,
        technician_name=t.assigned_technician.full_name if t.assigned_technician else "Unassigned"
    )

@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    t = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")

    num = t.ticket_number
    db.delete(t)
    db.commit()

    log_audit(
        db, action="TICKET_DELETED", resource=f"Ticket:{num}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Deleted ticket {num}"
    )
    return {"message": f"Ticket {num} deleted successfully"}
