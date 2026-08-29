from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.match import MatchCreate
from app.repositories.match_repo import MatchRepository
from app.repositories.game_event_repo import GameEventRepository

class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.match_repo = MatchRepository(db)
        self.event_repo = GameEventRepository(db)

    def create_match(self, match_in: MatchCreate, player_id: int):
        match = self.match_repo.create_match(match_in)
        self.event_repo.record_event("match_creation", player_id, match.id)
        self.db.commit()
        return match

    def join_match(self, match_id: int, player_id: int):
        match = self.match_repo.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        self.match_repo.join_match(match_id, player_id)
        self.event_repo.record_event("match_join", player_id, match_id)
        self.db.commit()
        return match

    def leave_match(self, match_id: int, player_id: int):
        success = self.match_repo.leave_match(match_id, player_id)
        if not success:
            raise HTTPException(status_code=400, detail="Not joined in match")
        
        self.event_repo.record_event("match_leave", player_id, match_id)
        self.db.commit()
        return {"detail": "Left match"}

    def get_match(self, match_id: int):
        match = self.match_repo.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return match
