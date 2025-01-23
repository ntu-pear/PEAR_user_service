from fastapi import APIRouter, Depends, HTTPException
from ..service import email_service as EmailService

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from ..schemas import email as email
import httpx

router = APIRouter()

# Request Email Confirmation
@router.post("/request-email-confirmation/")
async def request_email_confirmation(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = EmailService.generate_email_token(user.email)
    await EmailService.send_confirmation_email(user.email, token)
    # await send_email("test1","test2",user.email)
    return {"msg": "Confirmation email sent"}

# Confirm Email
@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        userDetails = EmailService.confirm_token(token)

    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == userDetails.get("email")).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.emailConfirmed = True
    db.commit()
    
    return {"msg": "Email confirmed"}