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


@app.on_event("startup")
def startup_event():
    from app.core.events import event_publisher
    from app.services.email import EmailService, MockEmailProvider, ImmediateEmailDispatcher
    from app.services.metrics import MetricsService
    from app.services.audit import AuditLogService
    import os
    if os.getenv("DB_NAME") == "docmind_test":
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        test_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    else:
        from app.db.session import SessionLocal as session_factory

    # 1. Instantiate services
    email_provider = MockEmailProvider()
    email_dispatcher = ImmediateEmailDispatcher(email_provider)
    email_service = EmailService(email_dispatcher)
    
    metrics_service = MetricsService()
    audit_service = AuditLogService(db_session_factory=session_factory)

    # 2. Register subscribers to global event publisher
    event_publisher.subscribe("USER_REGISTERED", email_service.handle_user_registered)
    event_publisher.subscribe("PASSWORD_RESET_REQUESTED", email_service.handle_password_reset_requested)
    
    event_publisher.subscribe("USER_REGISTERED", metrics_service.handle_user_registered)
    event_publisher.subscribe("EMAIL_VERIFIED", metrics_service.handle_email_verified)
    event_publisher.subscribe("LOGIN_SUCCESS", metrics_service.handle_login_success)
    event_publisher.subscribe("LOGIN_FAILED", metrics_service.handle_login_failed)
    event_publisher.subscribe("ACCOUNT_LOCKED", metrics_service.handle_account_locked)
    event_publisher.subscribe("PASSWORD_RESET_REQUESTED", metrics_service.handle_password_reset_requested)
    event_publisher.subscribe("PASSWORD_RESET_COMPLETED", metrics_service.handle_password_reset_completed)
    event_publisher.subscribe("SESSION_CREATED", metrics_service.handle_session_created)
    event_publisher.subscribe("SESSION_REVOKED", metrics_service.handle_session_revoked)

    # Register audit logs subscribers
    event_publisher.subscribe("LOGIN_SUCCESS", audit_service.handle_login_success)
    event_publisher.subscribe("LOGIN_FAILED", audit_service.handle_login_failed)
    event_publisher.subscribe("LOGOUT", audit_service.handle_logout)
    event_publisher.subscribe("PASSWORD_RESET_REQUESTED", audit_service.handle_password_reset_requested)
    event_publisher.subscribe("PASSWORD_RESET_COMPLETED", audit_service.handle_password_reset_completed)
    event_publisher.subscribe("EMAIL_VERIFIED", audit_service.handle_email_verified)
    event_publisher.subscribe("ACCOUNT_LOCKED", audit_service.handle_account_locked)

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


import uuid
from app.core.logging import request_context

@app.middleware("http")
async def log_requests_and_metrics(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    # Extract or generate request and correlation IDs
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    correlation_id = request.headers.get("x-correlation-id") or request_id
    
    # Extract user ID from bearer token if present
    user_id = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            from app.core.security import decode_token
            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub")
        except Exception:
            pass
            
    # Set context variables for request duration
    ctx_token = request_context.set({
        "request_id": request_id,
        "correlation_id": correlation_id,
        "user_id": user_id,
        "session_id": None,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    })
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        # Add correlation headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
    except Exception as e:
        status_code = 500
        logger.exception(f"Unhandled exception during request {method} {path}")
        raise e
    finally:
        latency = time.time() - start_time
        
        # Don't log metrics or base checks to prevent noise
        if path != "/metrics" and path != "/":
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
        request_context.reset(ctx_token)
        
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
