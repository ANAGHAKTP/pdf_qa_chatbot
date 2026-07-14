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
