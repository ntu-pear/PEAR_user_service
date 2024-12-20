from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PrivacyLevelSettingBase(BaseModel):
    roleId: int
    privacyLevelSensitive: int
    privacyLevelNonSensitive: int

class PrivacyLevelSettingCreate(PrivacyLevelSettingBase):
    privacyLevelSensitive: int
    privacyLevelNonSensitive: int

class PrivacyLevelSettingUpdate(PrivacyLevelSettingBase):
    pass

class PrivacyLevelSetting(PrivacyLevelSettingBase):
    id: int
    createdDate: datetime
    modifiedDate: datetime
    active: str

    class Config:
        orm_mode = True
