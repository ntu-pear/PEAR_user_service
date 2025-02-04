from ..schemas import email as email
import os
from itsdangerous import URLSafeTimedSerializer
from pysendpulse.pysendpulse import PySendPulse

OTP_EMAIL = os.getenv('OTP_EMAIL')
SECRET_KEY = os.getenv('SECRET_KEY')
SALT = os.getenv('SALT')
SPApiProxy = PySendPulse(os.getenv('SENDPULSE_API_KEY'), os.getenv('SENDPULSE_SECRET_KEY'))

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
    
    email = {
        'subject': 'Confirm Email',
        'html': f"Please click the following link to confirm your email: {confirmation_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    SPApiProxy.smtp_send_mail(email)

async def send_registration_email(email: str, token: str):
    registration_url = f"http://localhost:8000/user/register_account/{token}" 
    
    email = {
        'subject': 'Register Account',
        'html': f"Please click the following link to register your account: {registration_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    SPApiProxy.smtp_send_mail(email)

## Reset Password
async def send_reset_password_email(email: str, token: str):
    resetpassword_url = f"http://localhost:8000/forget-password/{token}"   
    email = {
        'subject': 'Reset Password',
        'html': f"Please click the following link to reset your password: {resetpassword_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    SPApiProxy.smtp_send_mail(email)
    
## Send 2FA email
async def send_2fa_email(email: str, code: int):
    email = {
        'subject': 'Verify your new PEAR account',
        'html': f"To verify your account, please use the following One Time Password (OTP): <b>{code}</b>",
        'text': f"To verify your account, please use the following One Time Password (OTP): {code}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    SPApiProxy.smtp_send_mail(email)