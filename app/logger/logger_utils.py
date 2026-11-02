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
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"


EXCLUDED_KEYS = {"CreatedById", "ModifiedById", "ModifiedDate", "CreatedDate", "IsDeleted", "isDeleted"}

# Sensitive fields that should be redacted in logs
SENSITIVE_KEYS = {"password", "currentPassword", "newPassword", "confirmPassword", "passwordHash", "token", "refresh_token", "access_token", "session_id"}


def filter_data(data: dict) -> dict:
    """Removes unwanted keys and redacts sensitive fields from the given dictionary."""
    if not data:
        return {}
    result = {}
    for k, v in data.items():
        if k in EXCLUDED_KEYS:
            continue
        if k in SENSITIVE_KEYS:
            result[k] = "[REDACTED]"
        else:
            result[k] = v
    return result


def serialize_data(data):
    """Recursively converts datetimes and nested structures to JSON-safe types."""
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    return data


# structured audit logger for CREATE/UPDATE/DELETE/AUTH events
def log_crud_action(
    action: ActionType,
    user: str,
    role: str,
    message: str,
    user_full_name: str = "",
    entity_id: Optional[str] = None,
    original_data: Optional[dict] = None,
    updated_data: Optional[dict] = None,
    table: str = 'user',
    log_type: str = "data",
    is_system_config: bool = False
):
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
        "log_type": log_type,
        "is_system_config": is_system_config,
    }

    logger.info("", extra=extra)


def log_user_login(user_id: str, user_full_name: str, role: str, session_id: str):
    """Logs a user login event with human-readable message."""
    log_crud_action(
        action=ActionType.LOGIN,
        user=user_id,
        user_full_name=user_full_name,
        role=role,
        entity_id=user_id,
        table="user",
        message=f"{user_full_name} logged in",
        log_type="auth",
        is_system_config=False,
    )


def log_user_logout(user_id: str, user_full_name: str, role: str):
    """Logs a user logout event with human-readable message."""
    log_crud_action(
        action=ActionType.LOGOUT,
        user=user_id,
        user_full_name=user_full_name,
        role=role,
        entity_id=user_id,
        table="user",
        message=f"{user_full_name} logged out",
        log_type="auth",
        is_system_config=False,
    )