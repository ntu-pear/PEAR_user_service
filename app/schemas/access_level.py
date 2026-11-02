from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AccessLevelBase(BaseModel):
    code: str
    levelRank: int
    levelName: str
    description: str

class AccessLevelCreate(AccessLevelBase):
    pass

class AccessLevelUpdate(BaseModel):
    code: Optional[str] = None
    levelRank: Optional[int] = None
    levelName: Optional[str] = None
    description: Optional[str] = None

class AccessLevelRead(AccessLevelBase):
    id: str
    isSystem: bool
    createdById: str
    createdDate: datetime
    modifiedById: str
    modifiedDate: datetime

    isEditable: Optional[bool] = None
    isDeletable: Optional[bool] = None

    class Config:
        orm_mode = True