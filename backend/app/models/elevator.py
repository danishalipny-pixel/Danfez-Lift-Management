from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Elevator(Base):
    __tablename__ = "elevators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "LIFT-A1"
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    floor_count = Column(Integer, default=10)
    current_floor = Column(Integer, default=1)
    target_floor = Column(Integer, default=1)
    status = Column(String(50), default="operational") # operational, moving, idle, maintenance, fault
    direction = Column(String(20), default="idle") # up, down, idle
    door_state = Column(String(20), default="closed") # open, closed, opening, closing
    speed_multiplier = Column(Float, default=1.0)
    emergency_stopped = Column(Boolean, default=False)
    last_maintenance_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    building = relationship("Building", back_populates="elevators")
    maintenance_tickets = relationship("MaintenanceTicket", back_populates="elevator", cascade="all, delete-orphan")
    fault_alerts = relationship("FaultAlert", back_populates="elevator", cascade="all, delete-orphan")
