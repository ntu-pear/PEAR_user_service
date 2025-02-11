from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    userId: str = None
    fullName: str = None
    roleName: str = None