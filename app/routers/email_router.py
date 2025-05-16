from fastapi import APIRouter, Depends, HTTPException
from ..service import email_service as EmailService

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from ..schemas import email as email

router = APIRouter()

#test send email
@router.get("/Test_send_email/")
async def test_send_email(email:str):
    token = EmailService.generate_email_token("12312fas", email)
    await EmailService.send_registration_email(email, token)
    return {"Email Sent"}