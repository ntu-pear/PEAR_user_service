from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import json
from app.crud.user_role_crud import get_user_role_by_user
from ..database import get_db
from ..schemas import user_auth
from ..schemas.user import UserRead,UserBase
from ..models.user_model import User
from ..service import user_auth_service
from ..schemas import user_auth


router = APIRouter()

@router.post("/login")#, response_model=user_auth.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userName == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not exist")
    if not user_auth_service.verify_password(form_data.password, user.passwordHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role=get_user_role_by_user(db=db,user_id=user.id)
    
    data={"userId":user.id,"roleId":role.roleId}
    data=json.dumps(data)
    access_token = user_auth_service.create_access_token(data={"sub": data})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/current_user", response_model=user_auth.TokenData)
def read_current_user(current_access: user_auth.TokenData = Depends(user_auth_service.get_current_user)):
    return current_access
