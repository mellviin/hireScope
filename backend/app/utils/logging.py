"""
Logging utilities
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
import os

def setup_logging(name: str) -> logging.Logger:
    """Setup JSON logging"""
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    
    # JSON handler
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(json_handler)
    
    return logger
