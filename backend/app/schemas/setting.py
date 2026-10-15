from typing import Optional
from pydantic import BaseModel, ConfigDict

class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None

class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SystemConfigUpdate(BaseModel):
    building_name: Optional[str] = None
    default_floors: Optional[int] = None
    simulation_speed: Optional[float] = None
    emergency_phone: Optional[str] = None
    maintenance_interval_days: Optional[int] = None
    email_notifications_enabled: Optional[bool] = None
