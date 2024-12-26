from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

class TempUserBase(BaseModel):
    #id: int
    firstName: str
    lastName: str
    preferredName: Optional[str] = None
    nric: str
    address: str
    dateOfBirth: date= Field("YYYY-MM-DD")
    gender: str
    contactNo: str
    email:str
    role:str

class CreateTempUser(TempUserBase):
    pass
    

class ReadTempUser(TempUserBase):
    id: int
    class Config:
        orm_mode = True


class UpdateTempUser(TempUserBase):
    pass