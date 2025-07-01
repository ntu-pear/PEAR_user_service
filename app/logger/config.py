from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_file = f"{LOG_DIR}/user_{today}.log"

log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "user": "%(user)s", "user_full_name": "%(user_full_name)s", "table": "%(table)s", "action": "%(action)s", "log_text": "%(log_text)s", "message": %(message)s}'
date_format = "%Y-%m-%dT%H:%M:%S"

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

logging.basicConfig(level=logging.INFO, handlers=[file_handler])

logger = logging.getLogger(__name__)