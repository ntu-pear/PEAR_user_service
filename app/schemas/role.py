from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RoleBase(BaseModel):
    roleName: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    roleName: Optional[str] = None
    active: Optional[str] = None

class RoleRead(RoleBase):
    id: int
    active: str
    createdById: Optional[int]=None
    createdDate: datetime
    modifiedById: Optional[int]=None
    modifiedDate: datetime
    pass

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }
