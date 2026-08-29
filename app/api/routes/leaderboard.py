from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.schemas.score import LeaderboardEntry
from app.api.dependencies import get_db
from app.services.score_service import ScoreService

router = APIRouter()

@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    score_service = ScoreService(db)
    return score_service.get_leaderboard()
