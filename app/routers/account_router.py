from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..crud import user_role_crud as crud_role_user
from ..crud import role_crud as role_crud
from ..schemas import account as schemas_account
from ..service.email_service import generate_confirmation_token, send_reset_password_email
from app.models.user_model import User
from ..service.email_service import *

router = APIRouter()

# Request password reset
@router.post("/request-reset-password/")
async def request_reset_confirmation(account: schemas_account.ResetPasswordBase, db: Session = Depends(get_db)):
    #user = db.query(User).filter(User.email == account.email).first()
    user = crud_user.get_user_by_email(db=db, email=account.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    RoleMap = crud_role_user.get_user_role_userId(db=db, user_Id = user.id)
    userRole = role_crud.get_role(db=db, roleId = RoleMap.roleId)
    
    if((user.nric != account.nric) | (user.dateOfBirth != account.dateOfBirth)| (userRole.role != account.userRole)):
        raise HTTPException(status_code=404, detail="Invalid Details")
    #if ((user.nric != account.nric) & user.nric != )
    token = generate_confirmation_token(user.email)
    await send_reset_password_email(user.email, token)
    # await send_email("test1","test2",user.email)
    return {"msg": "Reset password email sent"}