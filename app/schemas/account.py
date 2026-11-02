from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class UserResetPassword(BaseModel):
    newPassword: str
    confirmPassword: str


class RequestResetPasswordBase(UserResetPassword):
    """Identity (NRIC + DOB) plus the new password, verified and applied in
    a single step - there's no separate emailed-link step."""
    nric: str
    nric_DateOfBirth: date = Field("YYYY-MM-DD")

class UserChangePassword(UserResetPassword):
    currentPassword: str