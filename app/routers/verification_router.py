from fastapi import APIRouter, Depends, HTTPException
import pyotp
from captcha.image import ImageCaptcha
import random
import string
from ..service.email_service import send_2fa_email
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from app.service import user_auth_service as AuthService
from ..crud import session_crud as user_Session
import time

router = APIRouter()

# Request OTP
@router.post("/request-otp/")
async def request_otp(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    
    totp = pyotp.TOTP(pyotp.random_base32(), interval=900)
    user.OTP = totp.now()
    db.commit()
    try:
        await send_2fa_email(user_email, totp.now())
        return {"msg": "Confirmation email sent"}
    except:
        raise HTTPException(status_code=404, detail="Failed to send email")

# Verify otp
@router.get("/verify-otp/")
async def verify_otp(user_email: str, code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    
    if code == user.otp:
        user.otp = None
        user.otpFailedCount = 0
        db.commit()
        return user_Session.create_session(user, db)
    
    user.otpFailedCount += 1
    db.commit()
    
    if user.otpFailedCount > 4:
        user.otpFailedCount == 0
        user.otp = None
        db.commit()
        raise HTTPException(status_code=404, detail="Exceeded number of tries possible. Please request for a new OTP")
    
    return {"msg": "Invalid OTP"}

# Request Captcha
@router.post("/request-captcha/")
async def request_captcha(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
   
    captcha = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    user.captchaKey = captcha
    db.commit()
    image = ImageCaptcha(width = 280, height = 90)
    image.write(captcha, 'CAPTCHA.png')
    
    return {"msg": "Captcha generated"}

# Verify Captcha
@router.get("/verify-captcha/")
async def verify_captcha(user_email: str, captcha: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    
    if captcha == user.captchaKey:
        user.captchaKey = None
        user.captchaFailedCount = 0
        db.commit()
        return {"msg": "Captcha confirmed"}
    
    user.captchaFailedCount += 1
    db.commit()
    
    if user.captchaFailedCount > 4:
        user.captchaFailedCount == 0
        user.captchaKey = None
        db.commit()
        raise HTTPException(status_code=404, detail="Exceeded number of tries possible. Please request for a new captcha")
    
    return {"msg": "Wrong Captcha"}