from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..crud import user_role_crud as crud_role_user
from ..crud import role_crud as role_crud
from ..schemas import account as schemas_account
from ..service.email_service import generate_email_token, confirm_token
from ..service.account_service import send_resetpassword_email
from app.models.user_model import User
from ..service.email_service import *

router = APIRouter()

# Request password reset
@router.post("/account/request-reset-password/")
async def request_reset_confirmation(account: schemas_account.ResetPasswordBase, db: Session = Depends(get_db)):

    user = crud_user.get_user_by_email(db=db, email=account.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    fields_to_check = ["nric", "nric_DateOfBirth","roleName"]
    for field in fields_to_check:
        if getattr(user, field) != getattr(account, field):
            raise HTTPException(status_code=404, detail="Invalid Details")
        
    token = generate_email_token(user.email)
    await send_resetpassword_email(user.email, token)
  
    return {"msg": "Reset password email sent"}

@router.post("/account/reset_password/{token}")
async def reset_user_password(token: str, newPassword: str, confirmPassword: str, db: Session = Depends(get_db)):
    try:
        userDetails = confirm_token(token) 
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if (newPassword != confirmPassword):
        raise HTTPException(status_code=404, detail="Password do not match")
    
    user = db.query(User).filter(User.email == userDetails.get("email")).first()
    #return user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = newPassword
    db.commit()
    
    return {"Password Updated"}