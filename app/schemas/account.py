from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class AccountBase(BaseModel):
    nric_DateOfBirth: date = Field("YYYY-MM-DD")
    nric: str
    email: str
    roleName: str


class RequestResetPasswordBase(AccountBase):
    pass

class ResendEmail(AccountBase):
    pass

class UserResetPassword(BaseModel):
    newPassword: str
    confirmPassword: str

class UserChangePassword(UserResetPassword):
    currentPassword: str