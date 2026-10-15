from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class FaultAlert(Base):
    __tablename__ = "fault_alerts"

    id = Column(Integer, primary_key=True, index=True)
    fault_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "FLT-2026-101"
    elevator_id = Column(Integer, ForeignKey("elevators.id"), nullable=False)
    severity = Column(String(50), nullable=False, default="Medium") # Low, Medium, High, Critical
    category = Column(String(100), default="Door Sensor") # Door Sensor, Motor Drive, Safety Circuit, Brake Assembly, Power Surge, Leveling Alignment, Controller Logic
    description = Column(Text, nullable=False)
    
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    assigned_technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    elevator = relationship("Elevator", back_populates="fault_alerts")
    assigned_technician = relationship("Technician", back_populates="assigned_faults")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
