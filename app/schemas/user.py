from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from app.models.user_model import UserStatus
class UserBase(BaseModel):
    
    nric_FullName: str
    nric_Address: str
    nric_DateOfBirth: date= Field("YYYY-MM-DD")
    nric_Gender: str
    contactNo: str
    email: str
    roleName: str 

class UserCreate(UserBase):
    nric: str
    password:str
    
class TempUserCreate(UserBase):
    nric: str

class UserUpdate(BaseModel):
    nric_FullName: Optional[str] = None
    nric_Address: Optional[str] = None
    nric_DateOfBirth: Optional[date] = None
    nric_Gender: Optional[str] = None
    contactNo: Optional[str] = None
    allowNotification: Optional[bool] = None
    profilePicture: Optional[str] = None
    lockoutReason: Optional[str] = None
    status: Optional[UserStatus] = None
    email: Optional[str] = None

class UserRead(BaseModel):
    id:str
    nric_FullName: str
    nric: str
    nric_Address: str
    nric_DateOfBirth: date
    nric_Gender: str
    roleName: str
    contactNo: str
    allowNotification:bool
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    status:str
    email:str
    emailConfirmed:bool
    password:Optional[str]=None
    verified: bool
    active: bool
    twoFactorEnabled: bool
    createdById: Optional[str]=None
    createdDate: datetime
    modifiedById: Optional[str]=None
    modifiedDate: datetime
    

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }


