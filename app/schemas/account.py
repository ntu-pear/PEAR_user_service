from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class ResetPasswordBase(BaseModel):
    dateOfBirth: date = Field("YYYY-MM-DD")
    nric: str
    email: str
    userRole: str
