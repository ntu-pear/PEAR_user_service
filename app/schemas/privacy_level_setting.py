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
    createdById: str
    modifiedById: str
    createdDate: datetime
    modifiedDate: datetime
    active: str

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }
