from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class AccountBase(BaseModel):
    nric_DateOfBirth: date = Field("YYYY-MM-DD")
    nric: str
    email: str
    roleName: str


class UserResetPassword(BaseModel):
    newPassword: str
    confirmPassword: str


class RequestResetPasswordBase(AccountBase, UserResetPassword):
    """Identity (NRIC + DOB + email + role) plus the new password, verified
    and applied in a single step - there's no separate emailed-link step."""
    pass

class UserChangePassword(UserResetPassword):
    currentPassword: str