import json
import logging
import sys
import time
from datetime import datetime


import contextvars
from typing import Optional, Dict

# Context variable containing request correlation metadata
request_context: contextvars.ContextVar[Dict[str, Optional[str]]] = contextvars.ContextVar(
    "request_context", 
    default={
        "request_id": None, 
        "correlation_id": None, 
        "user_id": None, 
        "session_id": None, 
        "ip_address": None, 
        "user_agent": None
    }
)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "line_number": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Context-local correlation tracing fields
        ctx = request_context.get()
        for k, v in ctx.items():
            if v is not None:
                log_data[k] = v
            
        # Include custom log-specific attributes if present
        if hasattr(record, "response_time_ms"):
            log_data["response_time_ms"] = record.response_time_ms
        if hasattr(record, "user_id") and record.user_id is not None:
            log_data["user_id"] = record.user_id
            
        return json.dumps(log_data)


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    
    # Remove any default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    root_logger.addHandler(console_handler)
