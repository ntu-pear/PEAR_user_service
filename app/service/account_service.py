import os
from ..schemas import email as email
from mailjet_rest import Client

api_key = os.getenv('MAILERJET_API_KEY')
api_secret = os.getenv('MAILERJET_SECRET_KEY')

## Reset Password
async def send_resetpassword_email(email: str, token: str):
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
