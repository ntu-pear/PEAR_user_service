from sqlalchemy.orm import Session
from ..models.privacy_level_setting_model import PrivacyLevelSetting
from ..schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSettingUpdate

def get_privacy_level_setting(db: Session, privacy_setting_id: int):
    return db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_setting_id).first()

def get_privacy_level_settings(db: Session, skip: int = 0, limit: int = 10):
    return db.query(PrivacyLevelSetting).order_by(PrivacyLevelSetting.id).offset(skip).limit(limit).all()

def create_privacy_level_setting(db: Session, privacy_level_setting: PrivacyLevelSettingCreate):
    db_privacy_level_setting = PrivacyLevelSetting(**privacy_level_setting.dict())
    db.add(db_privacy_level_setting)
    db.commit()
    db.refresh(db_privacy_level_setting)
    return db_privacy_level_setting

def update_privacy_level_setting(db: Session, privacy_setting_id: int, privacy_level_setting: PrivacyLevelSettingUpdate):
    db_privacy_level_setting = db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_setting_id).first()
    if db_privacy_level_setting:
        for key, value in privacy_level_setting.dict().items():
            setattr(db_privacy_level_setting, key, value)
        db.commit()
        db.refresh(db_privacy_level_setting)
    return db_privacy_level_setting

def delete_privacy_level_setting(db: Session, privacy_setting_id: int):
    db_privacy_level_setting = db.query(PrivacyLevelSetting).filter(PrivacyLevelSetting.id == privacy_setting_id).first()
    if db_privacy_level_setting:
        db.delete(db_privacy_level_setting)
        db.commit()
    return db_privacy_level_setting
