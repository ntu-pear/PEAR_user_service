from fastapi import APIRouter, Depends, HTTPException
import pyotp
from captcha.image import ImageCaptcha
import random
import string
from ..service.email_service import send_2fa_email
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User

router = APIRouter()

# Request OTP
@router.post("/request-otp/")
async def request_otp(user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    
    totp = pyotp.TOTP(pyotp.random_base32(), interval=1000000)
    user.secretKey = totp.now()
    db.commit()
    await send_2fa_email(user_email, totp.now())
    
    return {"msg": "Confirmation email sent"}

# Verify OTP
@router.get("/verify-otp/")
async def verify_otp(user_email: str, code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
       raise HTTPException(status_code=404, detail="User not found")
    
    if code == user.secretKey:
        user.secretKey = None
        user.otpFailedCount = 0
        db.commit()
        return {"msg": "OTP confirmed"}
    
    user.otpFailedCount += 1
    db.commit()
    
    if user.otpFailedCount > 4:
        user.otpFailedCount == 0
        user.secretKey = None
        db.commit()
        return {"msg": "Exceeded number of tries possible. Please request for a new OTP"}
    
    return {"msg": "Wrong OTP"}

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
        return {"msg": "Exceeded number of tries possible. Please request for a new captcha"}
    
    return {"msg": "Wrong Captcha"}