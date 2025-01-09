from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class ResetPasswordBase(BaseModel):
    nric_DateOfBirth: date = Field("YYYY-MM-DD")
    nric: str
    email: str
    roleName: str
