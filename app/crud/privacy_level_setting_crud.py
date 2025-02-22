from sqlalchemy.orm import Session
from ..models.privacy_level_setting_model import PrivacyLevelSetting
from ..models.role_model import Role
from ..schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSettingUpdate

def get_privacy_level_setting_by_user(db: Session, privacy_user_id: str):
    return db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_user_id).first()

def get_privacy_level_settings_by_user(db: Session, skip: int = 0, limit: int = 10):
    return db.query(PrivacyLevelSetting).order_by(PrivacyLevelSetting.id).offset(skip).limit(limit).all()

def get_privacy_level_setting_by_role(db: Session, roleId: str):
    return db.query(Role).filter(Role.id == roleId).first()

def get_privacy_level_settings_by_role(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Role).order_by(Role.id).offset(skip).limit(limit).all()

#TODO: Created by + modified by should be from user
def create_privacy_level_setting(db: Session, privacy_level_setting: PrivacyLevelSettingCreate, created_by: int):
    db_privacy_level_setting = PrivacyLevelSetting(**privacy_level_setting.model_dump(),createdById=created_by,modifiedById=created_by)
    db.add(db_privacy_level_setting)
    db.commit()
    db.refresh(db_privacy_level_setting)
    return db_privacy_level_setting

def update_privacy_level_setting(db: Session, privacy_user_id: str, privacy_level_setting: PrivacyLevelSettingUpdate):
    db_privacy_level_setting = db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_user_id).first()
    if db_privacy_level_setting:
            # Update only provided fields
        for field, value in privacy_level_setting.model_dump(exclude_unset=True).items():
            setattr(db_privacy_level_setting, field, value)
        db.commit()
        db.refresh(db_privacy_level_setting)
    return db_privacy_level_setting

def delete_privacy_level_setting(db: Session, privacy_user_id: str):
    db_privacy_level_setting = db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_user_id).first()
    if db_privacy_level_setting:
        db.delete(db_privacy_level_setting)
        db.commit()
    return db_privacy_level_setting
