from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SecretQuestionBase(BaseModel):
    value: str

class SecretQuestionCreate(SecretQuestionBase):
    pass

class SecretQuestionUpdate(SecretQuestionBase):
    pass

class SecretQuestion(SecretQuestionBase):
    id: int
    createdDate: datetime
    modifiedDate: datetime
    active: str

    class Config:
        orm_mode = True
