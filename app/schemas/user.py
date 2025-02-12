from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.user_model import UserStatus, GenderStatus
class UserBase(BaseModel):
    
    nric_FullName: str
    nric_Address: str
    nric_DateOfBirth: date= Field("YYYY-MM-DD")
    nric_Gender: GenderStatus
    contactNo: str
    email: str
    roleName: str 

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
    lockoutReason: Optional[str] = None
    lockoutEnabled: Optional[bool]= None
    active: Optional[bool]=None
    status: Optional[UserStatus] = None
    email: Optional[str] = None
    roleName: Optional[str] = None

class UserUpdate_User(UserUpdate):
    twoFactorEnabled: Optional[bool]= None

class UserRead(BaseModel):
    id:str
    preferredName: Optional[str]=None
    nric_FullName: str
    nric: str
    nric_Address: str
    nric_DateOfBirth: date
    nric_Gender: GenderStatus
    roleName: str
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
    password:Optional[str]=None
    createdById: Optional[str]=None
    createdDate: datetime
    modifiedById: Optional[str]=None
    modifiedDate: datetime
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }


