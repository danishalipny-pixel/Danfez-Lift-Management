from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FaultAlertBase(BaseModel):
    elevator_id: int
    severity: str = "Medium" # Low, Medium, High, Critical
    category: str = "Door Sensor"
    description: str
    assigned_technician_id: Optional[int] = None

class FaultAlertCreate(FaultAlertBase):
    pass

class FaultAlertAcknowledge(BaseModel):
    assigned_technician_id: Optional[int] = None

class FaultAlertResolve(BaseModel):
    resolution_notes: str

class FaultAlertResponse(FaultAlertBase):
    id: int
    fault_code: str
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_id: Optional[int] = None
    is_resolved: bool
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    created_at: datetime
    elevator_name: Optional[str] = None
    elevator_code: Optional[str] = None
    technician_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
