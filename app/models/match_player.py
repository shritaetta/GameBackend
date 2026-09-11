from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class MatchPlayer(Base):
    __tablename__ = "match_players"

    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="players")
    player = relationship("Player", back_populates="matches")
