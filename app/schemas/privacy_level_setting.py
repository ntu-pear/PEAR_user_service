from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.privacy_level_setting_model import PrivacyStatus

class PrivacyLevelSettingBase(BaseModel):
    privacyLevelSensitive: Optional[PrivacyStatus] = None

class PrivacyLevelSettingCreate(PrivacyLevelSettingBase):
    active: Optional[bool] = None

class PrivacyLevelSettingUpdate(PrivacyLevelSettingBase):
    active: Optional[bool] = None

class PrivacyLevelSetting(PrivacyLevelSettingBase):
    id: str
    createdById: str
    modifiedById: str
    createdDate: datetime
    modifiedDate: datetime
    active: bool

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }
