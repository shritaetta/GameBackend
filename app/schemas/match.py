from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .player import PlayerResponse

class MatchBase(BaseModel):
    name: str

class MatchCreate(MatchBase):
    pass

class MatchResponse(MatchBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MatchDetailResponse(MatchResponse):
    players: List[PlayerResponse] = []
