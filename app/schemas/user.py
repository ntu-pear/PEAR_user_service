from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    #id: int
    
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    address: str
    dateOfBirth: date= Field("YYYY-MM-DD")
    gender: str
    contactNo: str
    email: str
    role: str 

class UserCreate(UserBase):
    nric: str
    passwordHash:str
    
    

class UserUpdate(UserBase):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    preferredName: Optional[str] = None
    address: Optional[str] = None
    dateOfBirth: Optional[date] = None
    gender: Optional[str] = None
    contactNo: Optional[str] = None
    allowNotification: Optional[str] = None
    profilePicture: Optional[str] = None
    lockoutReason: Optional[str] = None
    status: Optional[str] = None
    #userName: Optional[str] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None

class UserRead(BaseModel):
    id:int
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    nric: str
    address: str
    dateOfBirth: date
    gender: str
    contactNo: str
    allowNotification:str
    profilePicture: Optional[str]=None
    lockoutReason: Optional[str]=None
    status:str
    email:str
    emailConfirmed:str
    passwordHash:str

    twoFactorEnabled: str

    class Config:
        orm_mode = True


