from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.role_model import RolePrivacyStatus
from typing import List
class RoleBase(BaseModel):
    roleName: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    roleName: Optional[str] = None
    active: Optional[bool] = None

class RoleRead(RoleBase):
    id: str
    active: bool
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
    roles: List[RoleRead]

    class Config:
        orm_mode = True