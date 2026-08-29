from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.dependencies import get_db

router = APIRouter()

@router.get("")
def health_check(db: Session = Depends(get_db)):
    try:
        # Verify database connectivity
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
