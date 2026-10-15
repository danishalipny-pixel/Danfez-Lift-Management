from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MaintenanceTicketBase(BaseModel):
    elevator_id: int
    category: str = "Preventive Maintenance"
    priority: str = "Medium" # Low, Medium, High, Critical
    status: str = "Open" # Open, Assigned, In Progress, On Hold, Resolved, Closed
    description: str
    assigned_technician_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None

class MaintenanceTicketCreate(MaintenanceTicketBase):
    pass

class MaintenanceTicketUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    assigned_technician_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    completion_date: Optional[datetime] = None

class MaintenanceTicketResponse(MaintenanceTicketBase):
    id: int
    ticket_number: str
    created_by_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    elevator_name: Optional[str] = None
    elevator_code: Optional[str] = None
    technician_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
