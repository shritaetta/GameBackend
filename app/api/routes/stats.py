from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.services.player_service import PlayerService
from pydantic import BaseModel

router = APIRouter()

class StatsResponse(BaseModel):
    active_players: int
    cache_status: str

@router.get("", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    player_service = PlayerService(db)
    count, cache_status = player_service.get_active_player_count()
    return {"active_players": count, "cache_status": cache_status}
