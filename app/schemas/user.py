from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.user_model import UserStatus, GenderStatus
from typing import List

class UserBase(BaseModel):
    
    nric_FullName: str
    nric_Address: str
    nric_DateOfBirth: date= Field("YYYY-MM-DD")
    nric_Gender: GenderStatus
    contactNo: str
    email: str
    roleName: Optional[str] = None

class UserCreate(UserBase):
    nric: str
    password:str
    
class TempUserCreate(UserBase):
    nric: str

class UserUpdate(BaseModel):
    preferredName: Optional[str] = None
    contactNo: Optional[str] = None
    email: Optional[str] = None
class UserUpdate_Admin(UserUpdate):
    nric:Optional[str] = None
    nric_FullName: Optional[str] = None
    nric_Address: Optional[str] = None
    nric_DateOfBirth: Optional[date] = None
    nric_Gender: Optional[GenderStatus] = None
    lockOutReason: Optional[str] = None
    lockOutEnabled: Optional[bool]= None
    lockOutEnd : Optional[datetime]=None
    active: Optional[bool]=None
    status: Optional[UserStatus] = None
    email: Optional[str] = None
    roleName: Optional[str] = None
class UserUpdate_User(UserUpdate):
    twoFactorEnabled: Optional[bool]= None

class UpdateUsersRoleRequest(BaseModel):
    users_Id: List[str]
    role: str

class UserRead(BaseModel):
    id:str
    preferredName: Optional[str]=None
    nric_FullName: str
    nric: str
    nric_Address: str
    nric_DateOfBirth: date
    nric_Gender: GenderStatus
    roleName: Optional[str]=None
    contactNo: str
    allowNotification:bool
    profilePicture: Optional[str]=None
    status:UserStatus
    email:str
    emailConfirmed:bool
    verified: bool
    active: bool
    twoFactorEnabled: bool
class AdminRead(UserRead):
    lockOutEnabled: Optional[bool]=None
    lockoutReason: Optional[str]=None
    loginTimeStamp: Optional[datetime]=None
    lastPasswordChanged: Optional[datetime]=None
    #password:Optional[str]=None
    createdById: Optional[str]=None
    createdDate: datetime
    modifiedById: Optional[str]=None
    modifiedDate: datetime
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

class AdminSearch(BaseModel):
    id:Optional[str]=None
    preferredName: Optional[str]=None
    nric_FullName: Optional[str]=None
    nric: Optional[str]=None
    status:Optional[UserStatus]=None
    email:Optional[str]=None
    verified: Optional[bool]=None
    active:Optional[bool]=None
    twoFactorEnabled:Optional[bool]=None
    roleName: Optional[str]=None
    page: Optional[int] = 1  # Default to page 1
    page_size: Optional[int] = 10  # Default page size to 10

class SupervisorSearch(BaseModel):
    nric_FullName:str
class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    class Config:
        orm_mode = True
class UserPaginationResponse(PaginationResponse):
    users: List[AdminRead]

class SupervisorPaginationResponse(PaginationResponse):
    users: List[SupervisorSearch]