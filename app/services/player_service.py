from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.player import PlayerCreate, PlayerLogin
from app.repositories.player_repo import PlayerRepository
from app.repositories.game_event_repo import GameEventRepository
from app.core.security import verify_password, create_access_token

class PlayerService:
    def __init__(self, db: Session):
        self.db = db
        self.player_repo = PlayerRepository(db)
        self.event_repo = GameEventRepository(db)

    def register(self, player_in: PlayerCreate):
        if self.player_repo.get_player_by_username(player_in.username):
            raise HTTPException(status_code=400, detail="Username already registered")
        if self.player_repo.get_player_by_email(player_in.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        player = self.player_repo.create_player(player_in)
        self.event_repo.record_event("player_registration", player.id)
        self.db.commit()
        return player

    def login(self, player_in: PlayerLogin):
        player = self.player_repo.get_player_by_username(player_in.username)
        if not player or not verify_password(player_in.password, player.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": player.username})
        self.event_repo.record_event("login", player.id)
        self.db.commit()
        
        return {"access_token": access_token, "token_type": "bearer"}

    def get_current_player(self, username: str):
        player = self.player_repo.get_player_by_username(username)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return player
