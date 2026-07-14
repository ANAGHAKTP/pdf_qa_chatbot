import json
import logging
import sys
import time
from datetime import datetime


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
            
        # Include custom attributes if present
        if hasattr(record, "response_time_ms"):
            log_data["response_time_ms"] = record.response_time_ms
        if hasattr(record, "user_id"):
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
