from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RoleBase(BaseModel):
    id: int
    role: str
    createdDate: datetime
    modifiedDate: datetime
    active: str

class RoleCreate(RoleBase):
    role: str

class RoleUpdate(RoleBase):
    pass

class Role(RoleBase):
    role: str

    class Config:
        orm_mode = True
