from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class GameEvent(Base):
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(255), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="SET NULL"), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
