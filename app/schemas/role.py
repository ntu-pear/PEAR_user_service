from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RoleBase(BaseModel):
    id: int
    roleName: str
    createdDate: datetime
    modifiedDate: datetime
    active: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class Role(RoleBase):
    pass

    class Config:
        orm_mode = True
