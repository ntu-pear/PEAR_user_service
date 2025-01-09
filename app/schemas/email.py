from pydantic import BaseModel

class EmailBase(BaseModel):
    email: str
    subject: str
    body: str
