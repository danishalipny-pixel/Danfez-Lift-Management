import io
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.building import Building
from ..models.elevator import Elevator
from ..models.maintenance import MaintenanceTicket
from ..models.fault import FaultAlert
from ..models.technician import Technician
from ..models.audit import AuditLog
from ..models.user import User
from ..auth.dependencies import get_current_user, get_optional_current_user
from ..services.simulator_engine import simulator_manager

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])

@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    total_buildings = db.query(Building).count()
    elevators = db.query(Elevator).all()
    total_elevators = len(elevators)

    # Calculate operational vs maintenance vs faults based on active state
    operational_count = 0
    maintenance_count = 0
    fault_count = 0

    elevator_summaries = []
    for elev in elevators:
        sim = simulator_manager.simulators.get(elev.id)
        current_status = sim.status if sim else elev.status
        current_floor = sim.current_floor if sim else elev.current_floor
        direction = sim.direction if sim else elev.direction
        door_state = sim.door_state if sim else elev.door_state

        if current_status == "operational" or current_status == "moving" or current_status == "idle":
            operational_count += 1
        elif current_status == "maintenance":
            maintenance_count += 1
        elif current_status == "fault":
            fault_count += 1
        else:
            operational_count += 1

        elevator_summaries.append({
            "id": elev.id,
            "name": elev.name,
            "code": elev.code,
            "current_floor": current_floor,
            "direction": direction,
            "door_state": door_state,
            "status": current_status,
            "building_name": elev.building.name if elev.building else "Main Building",
            "floor_count": elev.floor_count
        })

    active_faults = db.query(FaultAlert).filter(FaultAlert.is_resolved == False).count()
    open_tickets = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.status.in_(["Open", "Assigned", "In Progress"])
    ).count()

    # Fault severity breakdown
    fault_severities = {
        "Critical": db.query(FaultAlert).filter(FaultAlert.severity == "Critical", FaultAlert.is_resolved == False).count(),
        "High": db.query(FaultAlert).filter(FaultAlert.severity == "High", FaultAlert.is_resolved == False).count(),
        "Medium": db.query(FaultAlert).filter(FaultAlert.severity == "Medium", FaultAlert.is_resolved == False).count(),
        "Low": db.query(FaultAlert).filter(FaultAlert.severity == "Low", FaultAlert.is_resolved == False).count()
    }

    # Availability calculation (simulated 98.4% or calculated from active vs total)
    availability_rate = round((operational_count / max(total_elevators, 1)) * 100, 1)

    # Recent activity from audit logs
    recent_activity = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    activity_list = [
        {
            "id": a.id,
            "action": a.action,
            "resource": a.resource,
            "user_email": a.user_email,
            "details": a.details,
            "timestamp": a.timestamp.strftime("%b %d, %H:%M")
        }
        for a in recent_activity
    ]

    # Upcoming maintenance schedule
    upcoming_schedule = db.query(MaintenanceTicket).filter(
        MaintenanceTicket.status.in_(["Open", "Assigned", "In Progress"])
    ).order_by(MaintenanceTicket.scheduled_date.asc()).limit(5).all()

    schedule_list = [
        {
            "ticket_number": t.ticket_number,
            "elevator_code": t.elevator.code if t.elevator else "",
            "category": t.category,
            "priority": t.priority,
            "scheduled_date": t.scheduled_date.strftime("%b %d, %Y") if t.scheduled_date else "Not Scheduled",
            "technician": t.assigned_technician.full_name if t.assigned_technician else "Unassigned"
        }
        for t in upcoming_schedule
    ]

    return {
        "total_buildings": total_buildings,
        "total_elevators": total_elevators,
        "elevators_operational": operational_count,
        "elevators_under_maintenance": maintenance_count,
        "elevators_fault": fault_count,
        "active_faults": active_faults,
        "open_maintenance_tasks": open_tickets,
        "availability_rate": availability_rate,
        "fault_severities": fault_severities,
        "elevators": elevator_summaries,
        "recent_activity": activity_list,
        "upcoming_schedule": schedule_list,
        "is_simulation_mode": True,
        "system_status": "ONLINE"
    }

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    # 1. Faults by severity
    severity_counts = {
        "Critical": db.query(FaultAlert).filter(FaultAlert.severity == "Critical").count(),
        "High": db.query(FaultAlert).filter(FaultAlert.severity == "High").count(),
        "Medium": db.query(FaultAlert).filter(FaultAlert.severity == "Medium").count(),
        "Low": db.query(FaultAlert).filter(FaultAlert.severity == "Low").count()
    }

    # 2. Maintenance tasks by status
    statuses = ["Open", "Assigned", "In Progress", "On Hold", "Resolved", "Closed"]
    status_counts = {}
    for st in statuses:
        status_counts[st] = db.query(MaintenanceTicket).filter(MaintenanceTicket.status == st).count()

    # 3. Monthly maintenance activity (Past 6 months simulated dataset based on database)
    monthly_labels = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    monthly_tickets = [12, 19, 14, 18, 22, max(db.query(MaintenanceTicket).count(), 16)]
    monthly_faults = [8, 11, 7, 9, 14, max(db.query(FaultAlert).count(), 10)]

    # 4. Elevator availability comparison
    elevators = db.query(Elevator).all()
    elevator_uptime = []
    for e in elevators:
        # Realistic uptime scores
        uptime = 99.4 if e.status == "operational" else (96.5 if e.status == "maintenance" else 94.2)
        elevator_uptime.append({
            "code": e.code,
            "name": e.name,
            "uptime_percentage": uptime,
            "status": e.status
        })

    return {
        "faults_by_severity": severity_counts,
        "maintenance_by_status": status_counts,
        "monthly_trend": {
            "labels": monthly_labels,
            "tickets": monthly_tickets,
            "faults": monthly_faults
        },
        "elevator_uptime": elevator_uptime,
        "is_demo_data": True
    }

@router.get("/export/{export_type}")
def export_csv(export_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)

    if export_type == "tickets":
        writer.writerow(["Ticket Number", "Elevator Code", "Category", "Priority", "Status", "Description", "Technician", "Created At", "Scheduled Date", "Resolved Date"])
        tickets = db.query(MaintenanceTicket).all()
        for t in tickets:
            writer.writerow([
                t.ticket_number,
                t.elevator.code if t.elevator else "",
                t.category,
                t.priority,
                t.status,
                t.description,
                t.assigned_technician.full_name if t.assigned_technician else "Unassigned",
                t.created_at.strftime("%Y-%m-%d %H:%M"),
                t.scheduled_date.strftime("%Y-%m-%d") if t.scheduled_date else "",
                t.completion_date.strftime("%Y-%m-%d") if t.completion_date else ""
            ])
        filename = f"danfez_maintenance_tickets_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    elif export_type == "faults":
        writer.writerow(["Fault Code", "Elevator Code", "Severity", "Category", "Description", "Acknowledged", "Resolved", "Created At", "Resolved At"])
        faults = db.query(FaultAlert).all()
        for f in faults:
            writer.writerow([
                f.fault_code,
                f.elevator.code if f.elevator else "",
                f.severity,
                f.category,
                f.description,
                "Yes" if f.is_acknowledged else "No",
                "Yes" if f.is_resolved else "No",
                f.created_at.strftime("%Y-%m-%d %H:%M"),
                f.resolved_at.strftime("%Y-%m-%d %H:%M") if f.resolved_at else ""
            ])
        filename = f"danfez_fault_alerts_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    elif export_type == "technicians":
        writer.writerow(["Name", "Email", "Phone", "Skills", "Certification", "Status"])
        techs = db.query(Technician).all()
        for tech in techs:
            writer.writerow([
                tech.full_name,
                tech.email,
                tech.phone,
                tech.skills,
                tech.certification_level,
                tech.status
            ])
        filename = f"danfez_technicians_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    elif export_type == "audit":
        writer.writerow(["Timestamp", "User Email", "Action", "Resource", "Details", "IP Address"])
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        for l in logs:
            writer.writerow([
                l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                l.user_email,
                l.action,
                l.resource,
                l.details or "",
                l.ip_address
            ])
        filename = f"danfez_audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    else:
        raise HTTPException(status_code=400, detail="Invalid export type. Supported: tickets, faults, technicians, audit")

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
