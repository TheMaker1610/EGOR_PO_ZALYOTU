from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserRead(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    must_change_password: bool
    failed_attempts: int
    locked_until: Optional[datetime]
    created_at: Optional[datetime]
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
