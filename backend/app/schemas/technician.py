from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class TechnicianBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    skills: str = "Traction Elevators, Door Operators, Safety Gears"
    certification_level: str = "Level 2 Certified Elevator Technician"
    status: str = "Active"
    notes: Optional[str] = None
    user_id: Optional[int] = None

class TechnicianCreate(TechnicianBase):
    pass

class TechnicianUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    skills: Optional[str] = None
    certification_level: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class TechnicianResponse(TechnicianBase):
    id: int
    created_at: datetime
    updated_at: datetime
    active_tickets_count: Optional[int] = 0
    completed_tickets_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
