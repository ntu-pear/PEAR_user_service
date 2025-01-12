from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.email_utils import DefaultChecker
from fastapi_mail.errors import ConnectionErrors
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

## Reset Password
async def send_resetpassword_email(email: str, token: str):
    resetpassword_url = f"http://localhost:8000/forget-password/{token}"
    message = MessageSchema(
        subject="Reset Password",
        recipients=[email],  # List of recipients, as a list
        body=f"Please click the following link to reset your password: {resetpassword_url}",
        subtype="html"
    )

    fm = FastMail(config)
    await fm.send_message(message)
