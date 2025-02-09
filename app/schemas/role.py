from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.role_model import Role_Names, RoleStatus
class RoleBase(BaseModel):
    roleName: Role_Names

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    roleName: Optional[Role_Names] = None
    active: Optional[RoleStatus] = None

class RoleRead(RoleBase):
    id: str
    active: RoleStatus
    createdById: Optional[str]=None
    createdDate: datetime
    modifiedById: Optional[str]=None
    modifiedDate: datetime
    pass

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }
