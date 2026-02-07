from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.admin_config_model import AdminConfig

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
    config_row = db.query(AdminConfig).first()
    config_cache = dict(config_row.configBlob) if config_row and config_row.configBlob else {}
    return config_cache


def get_all_configs(db: Session) -> Dict[str, ConfigValue]:
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


def update_all_configs(db: Session, new_configs: Dict[str, ConfigValue], modified_by_id: str) -> Dict[str, ConfigValue]:
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
    config_row = db.query(AdminConfig).first()

    if config_row is None:
        config_row = AdminConfig(configBlob=new_configs, modifiedById=modified_by_id)
        db.add(config_row)
    else:
        config_row.configBlob = new_configs
        config_row.modifiedById = modified_by_id

    db.commit()
    config_cache = dict(new_configs)
    return config_cache
