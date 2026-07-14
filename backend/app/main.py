import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_LATENCY, metrics_app
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.models import Base

# Setup structured JSON logging
setup_logging()
logger = logging.getLogger("app")

# Auto-create tables (Alembic is preferred for production, but this ensures the DB works out-of-the-box)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Could not auto-create database tables: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
origins = []
if settings.CORS_ORIGINS:
    if isinstance(settings.CORS_ORIGINS, list):
        origins = settings.CORS_ORIGINS
    else:
        origins = [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def log_requests_and_metrics(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    # Don't log metrics or base check requests to prevent noise
    if path == "/metrics" or path == "/":
        return await call_next(request)
        
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        logger.exception(f"Unhandled exception during request {method} {path}")
        raise e
    finally:
        latency = time.time() - start_time
        
        # Record Prometheus metrics
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status_code=status_code).inc()
        HTTP_REQUEST_LATENCY.labels(method=method, endpoint=path).observe(latency)
        
        # Log structured request completion
        logger.info(
            f"Request completed: {method} {path} - {status_code}",
            extra={
                "response_time_ms": round(latency * 1000, 2),
                "status_code": status_code
            }
        )
        
    return response


# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
