from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSettingUpdate, PrivacyLevelSetting
from ..crud.privacy_level_setting_crud import get_privacy_level_setting, get_privacy_level_settings, create_privacy_level_setting, update_privacy_level_setting, delete_privacy_level_setting
from ..database import get_db

router = APIRouter()

@router.get("/privacy_settings/{setting_id}", response_model=PrivacyLevelSetting)
def read_privacy_level_setting(setting_id: int, db: Session = Depends(get_db)):
    db_privacy_setting = get_privacy_level_setting(db, privacy_setting_id=setting_id)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy setting not found")
    return db_privacy_setting

@router.get("/privacy_settings", response_model=list[PrivacyLevelSetting])
def read_privacy_level_settings(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    privacy_settings = get_privacy_level_settings(db, skip=skip, limit=limit)
    return privacy_settings

@router.post("/privacy_settings", response_model=PrivacyLevelSetting)
def create_new_privacy_level_setting(privacy_level_setting: PrivacyLevelSettingCreate, db: Session = Depends(get_db)):
    return create_privacy_level_setting(db=db, privacy_level_setting=privacy_level_setting)

@router.put("/privacy_settings/{setting_id}", response_model=PrivacyLevelSetting)
def update_existing_privacy_level_setting(setting_id: int, privacy_level_setting: PrivacyLevelSettingUpdate, db: Session = Depends(get_db)):
    db_privacy_setting = update_privacy_level_setting(db, privacy_setting_id=setting_id, privacy_level_setting=privacy_level_setting)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy setting not found")
    return db_privacy_setting

@router.delete("/privacy_settings/{setting_id}", response_model=PrivacyLevelSetting)
def delete_privacy_level_setting(setting_id: int, db: Session = Depends(get_db)):
    db_privacy_setting = delete_privacy_level_setting(db, privacy_setting_id=setting_id)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy setting not found")
    return db_privacy_setting
