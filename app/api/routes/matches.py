from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.match import MatchCreate, MatchResponse, MatchDetailResponse
from app.api.dependencies import get_db, get_current_user
from app.services.match_service import MatchService
from app.models.player import Player

router = APIRouter()

@router.post("", response_model=MatchResponse, status_code=201)
def create_match(match_in: MatchCreate, db: Session = Depends(get_db), current_user: Player = Depends(get_current_user)):
    match_service = MatchService(db)
    return match_service.create_match(match_in, current_user.id)

@router.post("/{match_id}/join", response_model=MatchResponse)
def join_match(match_id: int, db: Session = Depends(get_db), current_user: Player = Depends(get_current_user)):
    match_service = MatchService(db)
    return match_service.join_match(match_id, current_user.id)

@router.post("/{match_id}/leave")
def leave_match(match_id: int, db: Session = Depends(get_db), current_user: Player = Depends(get_current_user)):
    match_service = MatchService(db)
    return match_service.leave_match(match_id, current_user.id)
