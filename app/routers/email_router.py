from fastapi import APIRouter, Depends, HTTPException
from ..service.email_service import generate_confirmation_token, confirm_token,send_confirmation_email
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User

router = APIRouter()

# Request Email Confirmation
@router.post("/request-email-confirmation/")
async def request_email_confirmation(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = generate_confirmation_token(user.email)
    
    await send_confirmation_email(user.email, token)
    return {"msg": "Confirmation email sent"}

# Confirm Email
@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        email = confirm_token(token)
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.emailConfirmed = True
    db.commit()
    
    return {"msg": "Email confirmed"}