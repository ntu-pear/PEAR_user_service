from datetime import datetime
import json
from enum import Enum
from typing import Optional
from .config import logger  # <-- import the dedicated audit logger

class ActionType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

EXCLUDED_KEYS = {"CreatedById", "ModifiedById", "ModifiedDate", "CreatedDate", "IsDeleted", "isDeleted"}

def filter_data(data: dict) -> dict:
    """Removes unwanted keys from the given dictionary."""
    return {k: v for k, v in data.items() if k not in EXCLUDED_KEYS} if data else {}

def serialize_data(data):
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    return data


def log_crud_action(
        action: ActionType,
        user: str,
        role: str,
        message: str,
        entity_id: Optional[str] = None,  # changed to str (since roleId is a string)
        original_data: Optional[dict] = None,
        updated_data: Optional[dict] = None,
):
    # Normalize data depending on action
    if action == ActionType.CREATE:
        original_data = None
    elif action == ActionType.DELETE:
        updated_data = None

    # Prepare structured log payload
    log_data = {
        "entity_id": entity_id,
        "original_data": filter_data(serialize_data(original_data)),
        "updated_data": filter_data(serialize_data(updated_data)),
    }

    # Extra metadata (these get picked up by JsonFormatter)
    extra = {
        "user": user,
        "role": role,
        "action": action.value,
        "log_text": message,
    }

    logger.info(json.dumps(log_data), extra=extra)
