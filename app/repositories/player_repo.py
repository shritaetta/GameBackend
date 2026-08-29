from sqlalchemy.orm import Session
from app.models.player import Player
from app.schemas.player import PlayerCreate
from app.core.security import get_password_hash

class PlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_player(self, player_id: int):
        return self.db.query(Player).filter(Player.id == player_id).first()

    def get_player_by_username(self, username: str):
        return self.db.query(Player).filter(Player.username == username).first()

    def get_player_by_email(self, email: str):
        return self.db.query(Player).filter(Player.email == email).first()

    def create_player(self, player: PlayerCreate):
        hashed_password = get_password_hash(player.password)
        db_player = Player(username=player.username, email=player.email, hashed_password=hashed_password)
        self.db.add(db_player)
        self.db.flush() # Flush to get ID, caller will commit
        return db_player
