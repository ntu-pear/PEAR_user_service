from pydantic import BaseModel
from typing import Optional

# Base schema for shared attributes
class UserRoleBase(BaseModel):
    userId: int
    roleId: int

# Schema for creating a new UserRole
class UserRoleCreate(UserRoleBase):
    pass

# Schema for updating an existing UserRole
class UserRoleUpdate(UserRoleBase):
    pass

# Schema for reading (response model)
class UserRoleRead(UserRoleBase):
    id: int

    class Config:
        orm_mode = True
