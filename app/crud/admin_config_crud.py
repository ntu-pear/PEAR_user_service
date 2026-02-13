from typing import Optional

from sqlalchemy.orm import Session

from app.models.admin_config_model import AdminConfig
from app.schemas.admin_config import AdminConfigMap


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
) -> AdminConfigMap:
    config_row = get_admin_config_row(db)
    if not config_row:
        config_row = AdminConfig(
            configBlob=new_configs,
            createdById=modified_by_id,
            modifiedById=modified_by_id,
        )
        db.add(config_row)
    else:
        config_row.configBlob = new_configs
        config_row.modifiedById = modified_by_id

    db.commit()
    return dict(new_configs)
