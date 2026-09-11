from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.routes import api_router
from app.core.logger import logger
import time
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.metrics import gamepulse_requests_total, gamepulse_request_duration_seconds

app = FastAPI(title="GamePulse API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Prometheus metrics are being collected")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # We only want to track route paths if possible, but request.url.path is simpler and works for the basic requirement.
    # To avoid high cardinality, we usually map paths, but raw path is fine for this requirement.
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Do not track /metrics itself to avoid noise
    if request.url.path != "/metrics":
        gamepulse_requests_total.labels(
            method=request.method, 
            endpoint=request.url.path, 
            http_status=response.status_code
        ).inc()
        
        gamepulse_request_duration_seconds.labels(
            method=request.method, 
            endpoint=request.url.path
        ).observe(process_time)
        
    return response

@app.get("/metrics", include_in_schema=False)
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(api_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error for request {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
