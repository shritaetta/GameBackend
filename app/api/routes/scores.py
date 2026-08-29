from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.score import ScoreUpdate, ScoreResponse
from app.api.dependencies import get_db, get_current_user
from app.services.score_service import ScoreService
from app.models.player import Player

router = APIRouter()

@router.post("", response_model=ScoreResponse)
def update_score(score_in: ScoreUpdate, db: Session = Depends(get_db), current_user: Player = Depends(get_current_user)):
    score_service = ScoreService(db)
    return score_service.update_score(score_in, current_user.id)
