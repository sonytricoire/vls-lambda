"""
Configuration for structured logging in JSON format.
"""
import os
import json
import logging
import time
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.
    Adds additional fields like timestamp, level, and AWS request ID.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = 'vls-data-collector'
        
        # Add environment
        log_record['environment'] = os.environ.get('ENVIRONMENT', 'dev')
        
        # Add AWS request ID if available
        if hasattr(record, 'aws_request_id'):
            log_record['aws_request_id'] = record.aws_request_id

def setup_logging():
    """
    Configure structured JSON logging.
    """
    # Get log level from environment variable or default to INFO
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove default handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    # Create a handler for stdout
    handler = logging.StreamHandler()
    
    # Create formatter
    formatter = CustomJsonFormatter('%(message)s %(levelname)s %(name)s %(module)s %(funcName)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger