from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    match = relationship("Match", back_populates="scores")
    player = relationship("Player", back_populates="scores")
