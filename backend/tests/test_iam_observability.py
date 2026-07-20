import pytest
import uuid
import logging
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.logging import JSONFormatter, request_context
from app.services.metrics import MetricsService
from app.core.events import Event
from app.core import metrics


def test_tracing_headers_in_response(client):
    # Call me endpoint or login with correlation headers
    request_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "X-Request-ID": request_id,
            "X-Correlation-ID": correlation_id
        }
    )
    
    # Assert headers are propagated to response
    assert response.headers.get("X-Request-ID") == request_id
    assert response.headers.get("X-Correlation-ID") == correlation_id


def test_structured_json_logging_contains_tracing_context():
    # Setup test logger
    logger = logging.getLogger("test_structured_json")
    logger.setLevel(logging.INFO)
    
    from io import StringIO
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Set context variables manually
    ctx_token = request_context.set({
        "request_id": "req-12345",
        "correlation_id": "corr-54321",
        "user_id": 99,
        "session_id": "sess-abc",
        "ip_address": "1.1.1.1",
        "user_agent": "TestAgent"
    })

    try:
        logger.info("Test log statement")
    finally:
        request_context.reset(ctx_token)

    # Parse logged JSON line
    log_output = log_capture.getvalue().strip()
    log_json = json.loads(log_output)
    
    assert log_json["message"] == "Test log statement"
    assert log_json["request_id"] == "req-12345"
    assert log_json["correlation_id"] == "corr-54321"
    assert log_json["user_id"] == 99
    assert log_json["session_id"] == "sess-abc"
    assert log_json["ip_address"] == "1.1.1.1"
    assert log_json["user_agent"] == "TestAgent"


def test_metrics_service_event_handling():
    metrics_service = MetricsService()
    
    # Get current counter values
    before_logins = metrics.IAM_LOGINS_SUCCESS_TOTAL._value.get()
    before_failures = metrics.IAM_LOGINS_FAILED_TOTAL._value.get()
    
    # Simulate events
    success_event = Event(
        event_type="LOGIN_SUCCESS",
        payload={"email": "metrics@test.com"}
    )
    metrics_service.handle_login_success(success_event)
    
    failed_event = Event(
        event_type="LOGIN_FAILED",
        payload={"email": "metrics@test.com"}
    )
    metrics_service.handle_login_failed(failed_event)
    
    # Check counters incremented
    assert metrics.IAM_LOGINS_SUCCESS_TOTAL._value.get() == before_logins + 1
    assert metrics.IAM_LOGINS_FAILED_TOTAL._value.get() == before_failures + 1
