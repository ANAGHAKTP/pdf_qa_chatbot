from prometheus_client import Counter, Histogram, make_asgi_app

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "docmind_http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_LATENCY = Histogram(
    "docmind_http_request_latency_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"]
)

# AI Pipeline metrics
EMBEDDING_LATENCY = Histogram(
    "docmind_embedding_latency_seconds",
    "Vector embedding generation latency in seconds"
)

RETRIEVAL_LATENCY = Histogram(
    "docmind_retrieval_latency_seconds",
    "RAG document retrieval latency in seconds"
)

LLM_LATENCY = Histogram(
    "docmind_llm_latency_seconds",
    "LLM generation latency in seconds"
)

TOKEN_USAGE = Counter(
    "docmind_token_usage_total",
    "Total count of tokens processed by LLM"
)

# ASGI application for exposing Prometheus metrics
metrics_app = make_asgi_app()


# IAM Metrics
from prometheus_client import Gauge

IAM_LOGINS_SUCCESS_TOTAL = Counter("docmind_iam_logins_success_total", "Total successful login attempts")
IAM_LOGINS_FAILED_TOTAL = Counter("docmind_iam_logins_failed_total", "Total failed login attempts")
IAM_ACCOUNT_LOCKOUTS_TOTAL = Counter("docmind_iam_account_lockouts_total", "Total account lockout events")
IAM_VERIFICATION_EMAILS_SENT = Counter("docmind_iam_verification_emails_sent_total", "Total verification emails sent")
IAM_VERIFICATION_SUCCESS_TOTAL = Counter("docmind_iam_verification_success_total", "Total successful email verifications")
IAM_PASSWORD_RESET_REQUESTS = Counter("docmind_iam_password_reset_requests_total", "Total password reset requests initiated")
IAM_PASSWORD_RESET_SUCCESS = Counter("docmind_iam_password_reset_success_total", "Total successful password resets completed")

IAM_LOGIN_LATENCY_SECONDS = Histogram("docmind_iam_login_latency_seconds", "Login request processing latency in seconds")
IAM_VERIFICATION_LATENCY_SECONDS = Histogram("docmind_iam_verification_latency_seconds", "Email verification processing latency in seconds")
IAM_ACTIVE_SESSIONS = Gauge("docmind_iam_active_sessions_count", "Current count of active user sessions")

# Cleanup Metrics
CLEANUP_RUNS_TOTAL = Counter("docmind_cleanup_runs_total", "Total count of background cleanup runs", ["job_name", "status"])
CLEANUP_DELETED_RECORDS_TOTAL = Counter("docmind_cleanup_deleted_records_total", "Total count of records deleted by cleanup jobs", ["job_name"])
CLEANUP_DURATION_SECONDS = Histogram("docmind_cleanup_duration_seconds", "Cleanup job execution duration in seconds", ["job_name"])
