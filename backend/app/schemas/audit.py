from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = "127.0.0.1"
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
