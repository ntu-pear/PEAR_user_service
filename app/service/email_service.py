from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.email_utils import DefaultChecker
from fastapi_mail.errors import ConnectionErrors
from ..schemas import email as email

import httpx
import os
from pathlib import Path
from pydantic import EmailStr
from itsdangerous import URLSafeTimedSerializer

from mailjet_rest import Client
api_key = os.getenv('MAILERJET_API_KEY')
api_secret = os.getenv('MAILERJET_SECRET_KEY')
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
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    data = {
    'Messages': [
                    {
                            "From": {
                                    "Email": "choozhenhui@gmail.com",
                                    "Name": "FYP_PEAR"
                            },
                            "To": [
                                    {
                                            "Email": email
                                    }
                            ],
                            "Subject": "Reset Password",
                            "TextPart": f"Please click the following link to confirm your email: {confirmation_url}",
                    }
            ]
    }
    
    mailjet.send.create(data=data)

async def send_registration_email(email: str, token: str):
    registration_url = f"http://localhost:8000/user/register_account/{token}" 
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    data = {
    'Messages': [
                    {
                            "From": {
                                    "Email": "choozhenhui@gmail.com",
                                    "Name": "FYP_PEAR"
                            },
                            "To": [
                                    {
                                            "Email": email
                                    }
                            ],
                            "Subject": "Reset Password",
                            "TextPart": f"Please click the following link to register your account: {registration_url}",
                    }
            ]
    }
    
    mailjet.send.create(data=data)

## Reset Password
async def send_reset_password_email(email: str, token: str):
    resetpassword_url = f"http://localhost:8000/forget-password/{token}"   
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    data = {
    'Messages': [
                    {
                            "From": {
                                    "Email": "choozhenhui@gmail.com",
                                    "Name": "FYP_PEAR"
                            },
                            "To": [
                                    {
                                            "Email": email
                                    }
                            ],
                            "Subject": "Reset Password",
                            "TextPart": f"Please click the following link to reset your password: {resetpassword_url}",
                    }
            ]
    }
    
    mailjet.send.create(data=data)
    
## Send 2FA email
async def send_2fa_email(email: str, code: int):
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    data = {
    'Messages': [
                    {
                            "From": {
                                    "Email": "choozhenhui@gmail.com",
                                    "Name": "FYP_PEAR"
                            },
                            "To": [
                                    {
                                            "Email": email
                                    }
                            ],
                            "Subject": "Verify your new PEAR account",
                            "TextPart": f"To verify your account, please use the following One Time Password (OTP): {code}",
                            "HTMLPart": f"To verify your account, please use the following One Time Password (OTP): <b>{code}</b>",
                    }
            ]
    }
    
    mailjet.send.create(data=data)

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