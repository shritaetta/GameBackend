from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.score import Score
from app.models.player import Player

class ScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_score(self, match_id: int, player_id: int, increment_by: int):
        score = self.db.query(Score).filter_by(match_id=match_id, player_id=player_id).first()
        if not score:
            score = Score(match_id=match_id, player_id=player_id, score=increment_by)
            self.db.add(score)
        else:
            score.score += increment_by
        self.db.flush()
        return score

    def get_leaderboard(self, limit: int = 10):
        # Sum scores across all matches for each player
        results = (
            self.db.query(Player.id, Player.username, func.sum(Score.score).label('total_score'))
            .join(Score, Player.id == Score.player_id)
            .group_by(Player.id)
            .order_by(func.sum(Score.score).desc())
            .limit(limit)
            .all()
        )
        return [{"player_id": r[0], "username": r[1], "total_score":int(r[2] or 0)} for r in results]
