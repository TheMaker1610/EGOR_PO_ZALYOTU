from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    event_id: str
    timestamp: Optional[datetime]
    event_type: str
    component: str
    username: Optional[str]
    ip_address: Optional[str]
    details: Optional[str]

    class Config:
        from_attributes = True
