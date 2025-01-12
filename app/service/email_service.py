from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.email_utils import DefaultChecker
from fastapi_mail.errors import ConnectionErrors
from ..schemas import email as email

import httpx
import os
from pathlib import Path
from pydantic import EmailStr
from itsdangerous import URLSafeTimedSerializer


config = ConnectionConfig(
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_FROM = os.getenv('MAIL_FROM'),
    MAIL_PORT = int(os.getenv('MAIL_PORT')),
    MAIL_SERVER = os.getenv('MAIL_SERVER'),
    MAIL_STARTTLS= True if os.getenv('MAIL_STARTTLS')=="True" else False,
    MAIL_SSL_TLS= True if os.getenv('MAIL_SSL_TLS')=="True" else False,
    MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME'),
    USE_CREDENTIALS= True if os.getenv('USE_CREDENTIALS')=="True" else False,
    VALIDATE_CERTS= True if os.getenv('VALIDATE_CERTS')=="True" else False
)

SECRET_KEY = os.getenv('SECRET_KEY')
SALT = os.getenv('SALT')


def generate_email_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    payload = {"email": email}#, "userName": userName}
    return serializer.dumps(payload, salt=SALT)

def confirm_token(token: str, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        userDetails = serializer.loads(token, salt=SALT, max_age=expiration)
        
    except Exception as e:      
        return False
    return userDetails

async def send_confirmation_email(email: str, token: str):
    confirmation_url = f"http://localhost:8000/confirm-email/{token}"
    message = MessageSchema(
        subject="Email Confirmation",
        recipients=[email],  # List of recipients, as a list
        body=f"Please click the following link to confirm your email: {confirmation_url}",
        subtype="html"
    )

    fm = FastMail(config)
    await fm.send_message(message)

async def send_registration_email(email: str, token: str):
    registration_url = f"http://localhost:8000/user/register_account/{token}"
    message = MessageSchema(
        subject="Account Registration",
        recipients=[email],  # List of recipients, as a list
        body=f"Please click the following link to register your account: {registration_url}",
        subtype="html"
    )

    fm = FastMail(config)
    await fm.send_message(message)

## Reset Password
async def send_reset_password_email(email: str, token: str):
    resetpassword_url = f"http://localhost:8000/forget-password/{token}"
    message = MessageSchema(
        subject="Reset Password",
        recipients=[email],  # List of recipients, as a list
        body=f"Please click the following link to reset your password: {resetpassword_url}",
        subtype="html"
    )

    fm = FastMail(config)
    await fm.send_message(message)
    
## Send 2FA email
async def send_2fa_email(email: str, code: int):
    message = MessageSchema(
        subject="Verification Code",
        recipients=[email],  # List of recipients, as a list
        body=f"Your verification code is: {code}. Please note that the code will expire in 5 minutes.",
        subtype="html"
    )

    fm = FastMail(config)
    await fm.send_message(message)

#send email
def send_email(email: email.EmailBase):
    try:
        email_service_url = "http://localhost:8001/api/v1/send-email/"
        response = httpx.post(email_service_url, json=email.dict())
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except httpx.RequestError as e:
        raise RuntimeError(f"Request error: {e}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"HTTP error: {e.response.status_code} - {e.response.text}")