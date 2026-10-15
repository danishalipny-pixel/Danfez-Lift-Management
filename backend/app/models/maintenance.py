from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. "MNT-2026-001"
    elevator_id = Column(Integer, ForeignKey("elevators.id"), nullable=False)
    category = Column(String(100), default="Preventive Maintenance") # Preventive, Inspection, Cable/Motor, Door Sensor, Electrical, Software
    priority = Column(String(50), default="Medium") # Low, Medium, High, Critical
    status = Column(String(50), default="Open") # Open, Assigned, In Progress, On Hold, Resolved, Closed
    description = Column(Text, nullable=False)
    
    assigned_technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    scheduled_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    elevator = relationship("Elevator", back_populates="maintenance_tickets")
    assigned_technician = relationship("Technician", back_populates="assigned_tickets")
    creator = relationship("User", back_populates="created_tickets", foreign_keys=[created_by_id])
