from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.match_player import MatchPlayer
from app.schemas.match import MatchCreate

class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_match(self, match_id: int):
        return self.db.query(Match).filter(Match.id == match_id).first()

    def get_matches(self, skip: int = 0, limit: int = 100):
        return self.db.query(Match).offset(skip).limit(limit).all()

    def create_match(self, match: MatchCreate):
        db_match = Match(name=match.name)
        self.db.add(db_match)
        self.db.flush()
        return db_match

    def join_match(self, match_id: int, player_id: int):
        # Check if already joined
        existing = self.db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_id).first()
        if existing:
            return existing
        
        db_match_player = MatchPlayer(match_id=match_id, player_id=player_id)
        self.db.add(db_match_player)
        self.db.flush()
        return db_match_player
        
    def leave_match(self, match_id: int, player_id: int):
        db_match_player = self.db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_id).first()
        if db_match_player:
            self.db.delete(db_match_player)
            self.db.flush()
            return True
        return False
