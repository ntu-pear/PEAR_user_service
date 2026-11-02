from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.crud import admin_config_crud
from app.schemas.admin_config import AdminConfigMap

ConfigValue = Any
config_cache: Optional[Dict[str, ConfigValue]] = None


def _load_config_blob(db: Session) -> Dict[str, ConfigValue]:
    """
    Load the single config JSON blob from the database into cache.

    Args:
        db: Database session.

    Returns:
        Full configuration dictionary.
    """
    global config_cache
    config_cache = admin_config_crud.get_config_blob(db)
    return config_cache


def get_all_configs(db: Session) -> AdminConfigMap:
    """
    Retrieve all configurations from cache or database.

    Args:
        db: Database session.

    Returns:
        Full configuration dictionary.
    """
    if config_cache is None:
        return _load_config_blob(db)
    return config_cache


def update_all_configs(db: Session, new_configs: AdminConfigMap, modified_by_id: str) -> AdminConfigMap:
    """
    Replace the full configuration JSON blob and refresh cache.

    Args:
        db: Database session.
        new_configs: Full configuration dictionary to persist.
        modified_by_id: ID of user making the change.

    Returns:
        Updated configuration dictionary.
    """
    global config_cache
    config_cache = admin_config_crud.update_config_blob(
        db,
        new_configs,
        modified_by_id,
    )
    return config_cache
