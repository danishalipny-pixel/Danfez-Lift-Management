from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ElevatorBase(BaseModel):
    name: str
    code: str
    building_id: int
    floor_count: int = 10
    speed_multiplier: float = 1.0

class ElevatorCreate(ElevatorBase):
    pass

class ElevatorUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    floor_count: Optional[int] = None
    status: Optional[str] = None
    speed_multiplier: Optional[float] = None

class ElevatorResponse(ElevatorBase):
    id: int
    current_floor: int
    target_floor: int
    status: str
    direction: str
    door_state: str
    emergency_stopped: bool
    building_name: Optional[str] = None
    last_maintenance_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    request_queue: Optional[List[int]] = []

    model_config = ConfigDict(from_attributes=True)

class SimulatorCallRequest(BaseModel):
    floor: int

class SimulatorDoorRequest(BaseModel):
    action: str # "open" or "close"

class SimulatorSpeedRequest(BaseModel):
    speed_multiplier: float # 0.5, 1.0, 2.0, 5.0

class SimulatorTestFaultRequest(BaseModel):
    category: str
    severity: str = "High"
    description: str
