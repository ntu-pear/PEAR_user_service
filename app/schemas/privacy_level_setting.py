from pydantic import BaseModel
from datetime import datetime
from typing import Optional

#TODO: id should be retrieved from user auth
class PrivacyLevelSettingBase(BaseModel):
    id: str
    privacyLevelSensitive: Optional[int] = None

class PrivacyLevelSettingCreate(PrivacyLevelSettingBase):
    active: bool

class PrivacyLevelSettingUpdate(PrivacyLevelSettingBase):
    pass

class PrivacyLevelSetting(PrivacyLevelSettingBase):
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
