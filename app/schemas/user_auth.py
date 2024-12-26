from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    userId: int = None
    role: str = None


class TwoFACodeRequest(BaseModel):
    phone_no: str

class TwoFACodeVerification(BaseModel):
    phone_no: str
    code: str