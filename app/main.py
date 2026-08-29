from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.routes import api_router
from app.core.logger import logger

app = FastAPI(title="GamePulse API", version="1.0.0")

app.include_router(api_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error for request {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
