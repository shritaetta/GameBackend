from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.score import ScoreUpdate
from app.repositories.score_repo import ScoreRepository
from app.repositories.game_event_repo import GameEventRepository
from app.core.redis import get_cache, set_cache, delete_cache

class ScoreService:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRepository(db)
        self.event_repo = GameEventRepository(db)

    def update_score(self, score_in: ScoreUpdate, player_id: int):
        # We assume player_id is the user making the request (updating their own score for now, 
        # or an admin. In this simple version, players update their own score)
        score = self.score_repo.update_score(score_in.match_id, player_id, score_in.score)
        
        details = {"increment": score_in.score, "new_total": score.score}
        self.event_repo.record_event("score_update", player_id, score_in.match_id, details)
        
        self.db.commit()
        delete_cache("leaderboard")
        return score

    def get_leaderboard(self):
        cached_leaderboard = get_cache("leaderboard")
        if cached_leaderboard is not None:
            return cached_leaderboard
        
        leaderboard = self.score_repo.get_leaderboard()
        set_cache("leaderboard", leaderboard, ex=60)
        return leaderboard
