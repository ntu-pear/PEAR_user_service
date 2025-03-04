from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSettingUpdate, PrivacyLevelSetting
from ..crud.privacy_level_setting_crud import get_privacy_level_setting_by_user, get_privacy_level_settings_by_user, get_privacy_level_setting_by_role, get_privacy_level_settings_by_role, create_privacy_level_setting, update_privacy_level_setting, delete_privacy_level_setting
from ..database import get_db
from ..service import user_auth_service as AuthService
from ..schemas import user_auth

router = APIRouter()

@router.get("/privacy_settings_user/{user_id}", response_model=PrivacyLevelSetting)
def read_privacy_level_setting_by_user(user_id: str, db: Session = Depends(get_db)):
    db_privacy_setting = get_privacy_level_setting_by_user(db, privacy_user_id=user_id)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy user setting not found")
    return db_privacy_setting

@router.get("/privacy_settings_user", response_model=list[PrivacyLevelSetting])
def read_privacy_level_settings_by_user(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    privacy_settings = get_privacy_level_settings_by_user(db, skip=skip, limit=limit)
    return privacy_settings

@router.get("/privacy_settings_role/{user_id}", response_model=PrivacyLevelSetting)
def read_privacy_level_setting_by_role(user_id: str, db: Session = Depends(get_db)):
    db_privacy_setting = get_privacy_level_setting_by_role(db, roleId=user_id)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy role setting not found")
    return db_privacy_setting

@router.get("/privacy_settings_role", response_model=list[PrivacyLevelSetting])
def read_privacy_level_settings_by_role(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    privacy_settings = get_privacy_level_settings_by_role(db, skip=skip, limit=limit)
    return privacy_settings

#TODO: ask about rate limit
@router.post("/privacy_settings", response_model=PrivacyLevelSetting)
def create_new_privacy_level_setting(privacy_level_setting: PrivacyLevelSettingCreate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_guardian = current_user["roleName"] == "GUARDIAN"
    if not is_guardian:
        raise HTTPException(status_code=404, detail="User is not authorised")
    return create_privacy_level_setting(db=db, privacy_level_setting=privacy_level_setting, created_by=current_user["userId"])

@router.put("/privacy_settings/{user_id}", response_model=PrivacyLevelSetting)
def update_existing_privacy_level_setting(user_id: str, privacy_level_setting: PrivacyLevelSettingUpdate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_guardian = current_user["roleName"] == "GUARDIAN"
    if not is_guardian:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_privacy_setting = update_privacy_level_setting(db=db, privacy_user_id=user_id, privacy_level_setting=privacy_level_setting)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy setting not found")
    return db_privacy_setting

@router.delete("/privacy_settings/{user_id}", response_model=PrivacyLevelSetting)
def delete_existing_privacy_level_setting(user_id: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_guardian = current_user["roleName"] == "GUARDIAN"
    if not is_guardian:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_privacy_setting = delete_privacy_level_setting(db=db, privacy_user_id=user_id)
    if db_privacy_setting is None:
        raise HTTPException(status_code=404, detail="Privacy setting not found")
    return db_privacy_setting
