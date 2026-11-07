from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .access_level import AccessLevelRead

class RoleBase(BaseModel):
    roleName: str
    description: Optional[str] = None
    accessLevelId: str

class RoleCreate(RoleBase):
    pass

class RoleWithAccessLevelRead(RoleBase):
    """RoleBase plus the access level's numeric rank.

    Used by /roles/name/{roleName}, which other services call to find out
    how much a role is allowed to see. Kept separate from RoleBase so the
    create and update paths are unaffected.
    """
    accessLevelSensitive: Optional[int] = None

    class Config:
        from_attributes = True

class RoleUpdate(BaseModel):
    roleName: Optional[str] = None
    description: Optional[str] = None
    accessLevelId: Optional[str] = None
    isDeleted: Optional[bool] = None

class RoleRead(RoleBase):
    id: str
    isDeleted: bool
    createdById: Optional[str] = None
    createdDate: datetime
    modifiedById: Optional[str] = None
    modifiedDate: datetime
    accessLevel: Optional[AccessLevelRead] = None

    class Config:
        orm_mode = True

class RoleNameRead(BaseModel):
    roleName: str

class RolePaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int

class AdminRolePaginationResponse(RolePaginationResponse):
    roles: List[RoleRead]

class RoleNamePaginationResponse(RolePaginationResponse):
    roles: List[RoleNameRead]