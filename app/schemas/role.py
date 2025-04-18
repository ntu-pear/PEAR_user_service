from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.role_model import RolePrivacyStatus
from typing import List
class RoleBase(BaseModel):
    roleName: str
    accessLevelSensitive: RolePrivacyStatus

class RoleUpdate(BaseModel):
    roleName: Optional[str] = None
    isDeleted: Optional[bool] = None
    accessLevelSensitive: Optional[RolePrivacyStatus] = None

class RoleRead(RoleBase):
    id: str
    isDeleted: bool
    accessLevelSensitive: RolePrivacyStatus
    createdById: Optional[str]=None
    createdDate: datetime
    modifiedById: Optional[str]=None
    modifiedDate: datetime
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

class RolePaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    class Config:
        orm_mode = True

class AdminRolePaginationResponse(RolePaginationResponse):
    roles: List[RoleRead]

class RoleNamePaginationResponse(RolePaginationResponse):
    roles: List[RoleBase] #return name and privacylevel