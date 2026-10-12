from fastapi import APIRouter, Depends, HTTPException
from captcha.image import ImageCaptcha
import random
import string
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User

router = APIRouter()

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