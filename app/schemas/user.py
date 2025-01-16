from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

class UserBase(BaseModel):
    
    id: Optional[str] = None
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
    nric_Address: Optional[str] = None
    #nric_DateOfBirth: Optional[date] = None
    nric_Gender: Optional[str] = None
    contactNo: Optional[str] = None
    allowNotification: Optional[str] = None
    profilePicture: Optional[str] = None
    lockoutReason: Optional[str] = None
    status: Optional[str] = None
    email: Optional[str] = None

class UserRead(BaseModel):
    id:int
    nric_FullName: str
    nric: str
    nric_Address: str
    nric_DateOfBirth: date
    nric_Gender: str
    roleName: str
    contactNo: str
    allowNotification:str
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    status:str
    email:str
    emailConfirmed:str
    password:Optional[str]=None
    verified: str
    twoFactorEnabled: str
    createdById: Optional[int]=None
    createdDate: datetime
    modifiedById: Optional[int]=None
    modifiedDate: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }


