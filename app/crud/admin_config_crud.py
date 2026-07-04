from datetime import datetime
import logging
from typing import Any, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.admin_config_model import AdminConfig
from ..logger.logger_utils import serialize_data, log_crud_action, ActionType
from app.schemas.admin_config import AdminConfigMap
from ..service.outbox_service import get_outbox_service, generate_correlation_id

logger = logging.getLogger(__name__)



def _adminconfig_to_dict(config: AdminConfig) -> dict[str, Any]:
    """Convert admin config model to dictionary for messaging."""
    result = {}
    for key, value in config.__dict__.items():
        if key.startswith('_'):
            continue
        if hasattr(value, '__tablename__'):
            continue
        elif hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def _upsert_config_row(
    db: Session,
    new_configs: AdminConfigMap,
    modified_by_id: str,
) -> Tuple[AdminConfig, str, Optional[dict], Optional[dict], datetime]:
    """
    Create or update the AdminConfig row.

    Returns (config_row, event_type, original_config_dict, original_data_dict, timestamp).
    original_config_dict and original_data_dict are None for a CREATED event.
    """
    timestamp = datetime.now()
    config_row = get_admin_config_row(db)

    if not config_row:
        config_row = AdminConfig(
            configBlob=new_configs.root,
            modifiedById=modified_by_id,
            modifiedDate=timestamp,
        )
        db.add(config_row)
        db.flush()
        return config_row, "USERCONFIG_CREATED", None, None, timestamp

    original_config_dict = _adminconfig_to_dict(config_row)
    original_data_dict = {
        k: serialize_data(v)
        for k, v in config_row.__dict__.items()
        if not k.startswith("_")
    }

    config_row.configBlob = new_configs.root
    config_row.modifiedById = modified_by_id
    config_row.modifiedDate = timestamp
    db.flush()

    return config_row, "USERCONFIG_UPDATED", original_config_dict, original_data_dict, timestamp


def _compute_config_changes(
    original_config_dict: dict,
    new_configs: AdminConfigMap,
) -> dict:
    """
    Diff old and new configBlob values.
    Returns a dict of {key: {old, new}} for every key that changed.
    """
    old_blob = original_config_dict.get('configBlob', {}) or {}
    new_blob = new_configs.root
    changes = {}
    for key in set(old_blob.keys()) | set(new_blob.keys()):
        old_value = old_blob.get(key)
        new_value = new_blob.get(key)
        if old_value != new_value:
            changes[key] = {
                'old': serialize_data(old_value),
                'new': serialize_data(new_value),
            }
    return changes


def _create_outbox_event(
    db: Session,
    event_type: str,
    config_row: AdminConfig,
    changes: dict,
    original_config_dict: Optional[dict],
    modified_by_id: str,
    timestamp: datetime,
    correlation_id: str,
):
    """Build the event payload and write it to the outbox table."""
    if event_type == "USERCONFIG_CREATED":
        payload = {
            'event_type': event_type,
            'userconfig_id': config_row.id,
            'userconfig_data': _adminconfig_to_dict(config_row),
            'created_by': modified_by_id,
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id,
        }
        routing_key = f"patient.user.config.created.{config_row.id}"
    else:
        payload = {
            'event_type': event_type,
            'userconfig_id': config_row.id,
            'old_data': original_config_dict,
            'new_data': _adminconfig_to_dict(config_row),
            'changes': changes,
            'modified_by': modified_by_id,
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id,
        }
        routing_key = f"patient.user.config.updated.{config_row.id}"

    return get_outbox_service().create_event(
        db=db,
        event_type=event_type,
        aggregate_id=config_row.id,
        payload=payload,
        routing_key=routing_key,
        correlation_id=correlation_id,
        created_by=modified_by_id,
    )


def _log_config_action(
    event_type: str,
    config_row: AdminConfig,
    original_data_dict: Optional[dict],
    modified_by_id: str,
) -> None:
    """Write the audit log entry for a config create or update."""
    updated_data_dict = {
        k: serialize_data(v)
        for k, v in config_row.__dict__.items()
        if not k.startswith("_")
    }

    if event_type == "USERCONFIG_CREATED":
        log_crud_action(
            action=ActionType.CREATE,
            role='admin',
            user=modified_by_id,
            message="Admin config created",
            entity_id=config_row.id,
            original_data=None,
            updated_data=updated_data_dict,
        )
    else:
        log_crud_action(
            action=ActionType.UPDATE,
            role='admin',
            user=modified_by_id,
            message="Admin config updated",
            entity_id=config_row.id,
            original_data=original_data_dict,
            updated_data=updated_data_dict,
        )




def get_admin_config_row(db: Session) -> Optional[AdminConfig]:
    return db.query(AdminConfig).first()


def get_config_blob(db: Session) -> AdminConfigMap:
    config_row = get_admin_config_row(db)
    if config_row and config_row.configBlob:
        return dict(config_row.configBlob)
    return {}


def update_config_blob(
    db: Session,
    new_configs: AdminConfigMap,
    modified_by_id: str,
    correlation_id: str = None,
) -> AdminConfigMap:

    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Check for an existing row BEFORE writing anything.
        existing_row = get_admin_config_row(db)
        if existing_row:
            changes = _compute_config_changes(
                _adminconfig_to_dict(existing_row), new_configs
            )
            if not changes:
                logger.info(
                    f"No changes detected for Admin config ID {existing_row.id}, skipping update"
                )
                return new_configs.root

        # 2. Persist the new config values (either create or update) and get the event type and original config for messaging and logging.
        config_row, event_type, original_config_dict, original_data_dict, timestamp = _upsert_config_row(
            db, new_configs, modified_by_id
        )

        # 3. For the CREATE path changes is always empty (nothing to diff).
        if event_type == "USERCONFIG_CREATED":
            changes = {}

        # 4. Write outbox event
        outbox_event = _create_outbox_event(
            db, event_type, config_row, changes,
            original_config_dict, modified_by_id, timestamp, correlation_id,
        )

        # 5. Audit log
        _log_config_action(event_type, config_row, original_data_dict, modified_by_id)

        # 6. Commit both the config row and outbox event atomically
        db.commit()

        if event_type == "USERCONFIG_UPDATED":
            logger.info(f"Updated Admin config ID {config_row.id} with changes: {changes} and outbox event {outbox_event.id} (correlation: {correlation_id})")
        elif event_type == "USERCONFIG_CREATED":
            logger.info(f"Created Admin config ID {config_row.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")

        return new_configs.root

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating admin config: {str(e)}")
        raise
