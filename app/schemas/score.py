from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScoreBase(BaseModel):
    match_id: int
    score: int

class ScoreUpdate(ScoreBase):
    pass

class ScoreResponse(ScoreBase):
    id: int
    player_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    player_id: int
    username: str
    total_score: int
