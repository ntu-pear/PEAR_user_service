from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    nric: str
    address: str
    dateOfBirth: datetime
    gender: str
    contactNo: str
    #Why is this not boolean?
    allowNotification:str
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    loginTimeStamp: datetime
    lastPasswordChanged:datetime
    status:str
    userName:str
    email:str
    emailConfirmed:str
    passwordHash:str
    securityStamp:Optional[str]=None
    concurrencyStamp: Optional[str]=None
    phoneNumber: Optional[str]=None
    phoneNumberConfirmed:str
    twoFactorEnabled: str
    lockOutEnd: Optional[datetime]=None
    lockOutEnabled: Optional[str]=None
    accessFailedCount: Optional[int]=None

class UserCreate(UserBase):
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    nric: str
    address: str
    dateOfBirth: datetime
    gender: str
    contactNo: str
    allowNotification:str
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    status:str
    userName:str
    email:str
    emailConfirmed:str
    passwordHash:str
    phoneNumber: Optional[str]=None
    phoneNumberConfirmed:str
    twoFactorEnabled: str


class UserUpdate(UserBase):
    pass

class UserRead(UserBase):
    id:int
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    nric: str
    address: str
    dateOfBirth: datetime
    gender: str
    contactNo: str
    allowNotification:str
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    status:str
    userName:str
    email:str
    emailConfirmed:str
    passwordHash:str
    phoneNumber: Optional[str]=None
    phoneNumberConfirmed:str
    twoFactorEnabled: str

    class Config:
        orm_mode = True
