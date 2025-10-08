import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json
from datetime import datetime


LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_file = f"{LOG_DIR}/user_{today}.log"

#This class isn't functional yet, in process of implementing
class ConditionalFormatter(logging.Formatter):
    """
    Custom formatter that handles optional fields gracefully
    """

    def __init__(self, detailed_format, simple_format, datefmt=None):
        super().__init__(datefmt=datefmt)
        self.detailed_format = detailed_format
        self.simple_format = simple_format

    def format(self, record):
        # Check if this is a detailed log record with user info
        if hasattr(record, 'user') and hasattr(record, 'table'):
            # Use detailed format for CRUD operations
            formatter = logging.Formatter(self.detailed_format, datefmt=self.datefmt)
        else:
            # Use simple format for general logging
            formatter = logging.Formatter(self.simple_format, datefmt=self.datefmt)

        return formatter.format(record)

log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "user": "%(user)s", "action": "%(action)s", "log_text": "%(log_text)s", "message": %(message)s}'

# Detailed format for CRUD operations (when user context is available)
detailed_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "user": "%(user)s", "user_full_name": "%(user_full_name)s", "table": "%(table)s", "action": "%(action)s", "log_text": "%(log_text)s", "message": %(message)s}'

# Simple format for general logging (when user context is not available)
simple_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'

date_format = "%Y-%m-%dT%H:%M:%S"



file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

logging.basicConfig(level=logging.INFO, handlers=[file_handler])

logger = logging.getLogger(__name__)