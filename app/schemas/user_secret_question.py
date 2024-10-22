from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserSecretQuestionBase(BaseModel):
    userId: int
    secretQuestionId: int
    secretQuestionAnswer: str

class UserSecretQuestionCreate(UserSecretQuestionBase):
    pass

class UserSecretQuestionUpdate(UserSecretQuestionBase):
    pass

class UserSecretQuestion(UserSecretQuestionBase):
    id: int
    createdDate: datetime
    modifiedDate: datetime
    active: str

    class Config:
        orm_mode = True
