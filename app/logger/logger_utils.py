from datetime import datetime
import json
from enum import Enum
from typing import Optional
from .config import logger  # dedicated audit logger


class ActionType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"


EXCLUDED_KEYS = {"CreatedById", "ModifiedById", "ModifiedDate", "CreatedDate", "IsDeleted", "isDeleted"}


def filter_data(data: dict) -> dict:
    """Removes unwanted keys from the given dictionary."""
    return {k: v for k, v in data.items() if k not in EXCLUDED_KEYS} if data else {}


def serialize_data(data):
    """Recursively converts datetimes and nested structures to JSON-safe types."""
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    return data


# structured audit logger for CREATE/UPDATE/DELETE
def log_crud_action(action: ActionType, user: str, role: str, message: str,user_full_name: str = "", entity_id: Optional[str] = None,
                    original_data: Optional[dict] = None, updated_data: Optional[dict] = None, table='user'):
    """Logs a CRUD operation with consistent structured JSON fields."""
    if action == ActionType.CREATE:
        original_data = None
    elif action == ActionType.DELETE:
        updated_data = None

    log_data = {
        "entity_id": entity_id,
        "original_data": filter_data(serialize_data(original_data)),
        "updated_data": filter_data(serialize_data(updated_data)),
    }

    extra = {
        "user": user,
        "role": role,
        "action": action.value,
        "log_text": message,
        "table": table,
        "log_data": log_data,
        "user_full_name": user_full_name,
    }

    logger.info(json.dumps(log_data), extra=extra)


#To log when a user logins in
def log_user_login(user_id: str, user_full_name: str, role: str, session_id: str):
    """Logs a user login event with session metadata."""
    extra = {
        "user": user_id,
        "user_full_name": user_full_name,
        "role": role,
        "action": ActionType.LOGIN.value,
        "log_text": "User logged in",
        "log_data": {
            #"session_id": session_id,
            "loginTimeStamp": datetime.now().isoformat(),
        },
    }

    logger.info("", extra=extra)
