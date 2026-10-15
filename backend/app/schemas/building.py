from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class BuildingBase(BaseModel):
    name: str
    address: str
    total_floors: int = 10

class BuildingCreate(BuildingBase):
    pass

class BuildingResponse(BuildingBase):
    id: int
    created_at: datetime
    elevator_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
