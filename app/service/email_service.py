from ..schemas import email as email
from fastapi import HTTPException
import os
import re
from fastapi import HTTPException, status
from itsdangerous import URLSafeTimedSerializer
from pysendpulse.pysendpulse import PySendPulse

OTP_EMAIL = os.getenv('OTP_EMAIL')
SECRET_KEY = os.getenv('SECRET_KEY')
SALT = os.getenv('SALT')
_sendpulse_client = None


def _sendpulse():
    """Create the SendPulse client on first use, not at import.

    PySendPulse authenticates against the SendPulse API as soon as it is
    constructed. Doing that at import made the whole service fail to start
    (and CI fail) whenever SendPulse rejected the credentials; now only the
    email being sent fails, and the next send tries again.
    """
    global _sendpulse_client
    if _sendpulse_client is None:
        _sendpulse_client = PySendPulse(os.getenv('SENDPULSE_API_KEY'), os.getenv('SENDPULSE_SECRET_KEY'))
    return _sendpulse_client

EMAIL_LINK_BASEURL = os.getenv('EMAIL_LINK_BASEURL')

def generate_email_token(userId: str, email: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    payload = {"userId": userId,"email": email}#, "userName": userName}
    return serializer.dumps(payload, salt=SALT)


def confirm_token(token: str, expiration=600): #600 sec 10min expiry
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        userDetails = serializer.loads(token, salt=SALT, max_age=expiration)
        
    except Exception as e:      
        raise HTTPException(status_code=404, detail="Invalid Token")
    return userDetails

async def send_confirmation_email(email: str, token: str):
    validate_email_format(email)
    print("EMAIL_LINK_BASEURL used:", EMAIL_LINK_BASEURL)
    print("EMAIL_LINK_BASEURL =", os.getenv("EMAIL_LINK_BASEURL"))
    confirmation_url = f"{EMAIL_LINK_BASEURL}/confirm-email/{token}"
    
    email = {
        'subject': 'Confirm Email',
        'html': f"Please click the following link to confirm your email: {confirmation_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    _sendpulse().smtp_send_mail(email)

async def send_registration_email(email: str, token: str):
    validate_email_format(email)
    registration_url = f"{EMAIL_LINK_BASEURL}/user/register_account/{token}" 
    
    email = {
        'subject': 'Register Account',
        'html': f"Please click the following link to register your account: {registration_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    _sendpulse().smtp_send_mail(email)

## Reset Password
async def send_reset_password_email(email: str, token: str):
    validate_email_format(email)
    resetpassword_url = f"{EMAIL_LINK_BASEURL}/forget-password/{token}"   
    email = {
        'subject': 'Reset Password',
        'html': f"Please click the following link to reset your password: {resetpassword_url}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    _sendpulse().smtp_send_mail(email)
    
## Send 2FA email
async def send_2fa_email(email: str, code: int):
    validate_email_format(email)
    email = {
        'subject': 'Verify your new PEAR account',
        'html': f"To verify your account, please use the following One Time Password (OTP): <b>{code}</b>",
        'text': f"To verify your account, please use the following One Time Password (OTP): {code}",
        'from': {'name': 'FYP_PEAR', 'email': 'fyp_pear@techdevglobal.com'},
        'to': [
            {'email': email}
        ],
    }
    
    _sendpulse().smtp_send_mail(email)
    
#Check for valid email format
def validate_email_format(email: str):
    """
    Validate email with the following rules:
    - A valid email username
    - @
    - A valid domain name
    """
    if not re.match(r"^[-\w\.]+@([\w-]+\.)+[\w-]{2,4}$", email):
        raise HTTPException(
            status_code=404,
            detail=(
                "Invalid email format"
            )
        )