from sqlalchemy.orm import Session
from app.models.game_event import GameEvent

class GameEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_event(self, event_type: str, player_id: int = None, match_id: int = None, details: dict = None):
        db_event = GameEvent(
            event_type=event_type,
            player_id=player_id,
            match_id=match_id,
            details=details
        )
        self.db.add(db_event)
        self.db.flush()
        return db_event
