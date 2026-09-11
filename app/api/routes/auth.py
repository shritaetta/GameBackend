from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.player import PlayerCreate, PlayerLogin, PlayerResponse
from app.schemas.token import Token
from app.api.dependencies import get_db, get_current_user
from app.services.player_service import PlayerService
from app.models.player import Player

router = APIRouter()

@router.post("/register", response_model=PlayerResponse, status_code=201)
def register(player_in: PlayerCreate, db: Session = Depends(get_db)):
    player_service = PlayerService(db)
    return player_service.register(player_in)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    player_service = PlayerService(db)
    player_in = PlayerLogin(username=form_data.username, password=form_data.password)
    return player_service.login(player_in)

@router.get("/players/me", response_model=PlayerResponse)
def read_users_me(current_user: Player = Depends(get_current_user)):
    return current_user
