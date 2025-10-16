import logging
import os
import json
from datetime import datetime

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_file = f"{LOG_DIR}/user_{today}.log"

class ConditionalFormatter(logging.Formatter):
    """
    Outputs detailed JSON if 'user' and 'table' exist, otherwise simple JSON.
    """
    def __init__(self, datefmt=None):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt

    def format(self, record):
        log_dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name
        }


        # Check if this is a detailed log record
        if hasattr(record, 'user') and hasattr(record, 'table'):
            log_dict.update({
                "user": getattr(record, "user"),
                "user_full_name": getattr(record, "user_full_name", ""),
                "table": getattr(record, "table"),
                "action": getattr(record, "action", ""),
                "log_text": getattr(record, "log_text", ""),
                "message": getattr(record, "log_data", getattr(record, "message", None))
            })
        elif hasattr(record, "user"):
            log_dict.update({
                "user": getattr(record, "user"),
                "user_full_name": getattr(record, "user_full_name", ""),
                "role": getattr(record, "role", ""),
                "action": getattr(record, "action", ""),
                "log_text": getattr(record, "log_text", "")
            })
        else:
            log_dict["message"] = getattr(record, "message", record.getMessage())

        # Ensure message is valid JSON if it is a dict
        if isinstance(log_dict.get("message"), dict):
            log_dict["message"] = log_dict["message"]  # already a dict, keep as-is

        return json.dumps(log_dict)

# Handlers
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(ConditionalFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(ConditionalFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)



