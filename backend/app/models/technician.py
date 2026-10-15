from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base

class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Linked to a user account if exists
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    skills = Column(String(255), default="Traction Elevators, Door Operators, Safety Gears") # comma separated
    certification_level = Column(String(100), default="Level 2 Certified Elevator Technician")
    status = Column(String(50), default="Active") # Active, Inactive, On Leave
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="technician_profile")
    assigned_tickets = relationship("MaintenanceTicket", back_populates="assigned_technician")
    assigned_faults = relationship("FaultAlert", back_populates="assigned_technician")
