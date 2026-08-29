from fastapi import APIRouter
from .auth import router as auth_router
from .matches import router as matches_router
from .scores import router as scores_router
from .leaderboard import router as leaderboard_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(matches_router, prefix="/matches", tags=["matches"])
api_router.include_router(scores_router, prefix="/scores", tags=["scores"])
api_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(health_router, prefix="/health", tags=["health"])

# To satisfy the "GET /players/me" without auth prefix requirement, 
# although it's in auth_router, we can also expose it at /players if needed, 
# but auth_router handles it at /auth/players/me. 
# Let's add it explicitly to the root router just in case for strict compliance:
from .auth import read_users_me
api_router.add_api_route("/players/me", read_users_me, methods=["GET"], tags=["players"])
