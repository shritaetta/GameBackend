from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class PlayerBase(BaseModel):
    username: str
    email: EmailStr

class PlayerCreate(PlayerBase):
    password: str

class PlayerLogin(BaseModel):
    username: str
    password: str

class PlayerResponse(PlayerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
