from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..schemas import user_auth
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from app.models.user_model import User
import logging
import sys
import cloudinary
import cloudinary.uploader

# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit

global_bucket = TokenBucket(rate=5, capacity=10)

router = APIRouter(
    tags=["admin"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}

#Create Acc, unverified
@router.post("/admin/create_account/", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
async def create_user(user: schemas_user.TempUserCreate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user=crud_user.create_user(db=db, user=user, created_by=current_user["userId"])
    if db_user:
        #Send registration email
        token = EmailService.generate_email_token(db_user.id, db_user.email)
        await EmailService.send_registration_email(db_user.email, token)
   
    return db_user

@router.get("/admin/{userId}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
def read_user(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.get("/admin/", response_model=list[schemas_user.AdminRead])
@rate_limit(global_bucket, tokens_required=1)
def read_users(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    #Only Admin can read all users
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    
    return users

@router.get("/admin/get_email/{email}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
async def get_user_by_email(email: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/admin/{userId}", response_model=schemas_user.UserUpdate)
def update_user_by_admin(userId: str, user: schemas_user.UserUpdate_Admin,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.update_user_Admin(db=db, userId=userId, user=user,modified_by=current_user["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/admin/{userId}", response_model=schemas_user.UserBase)
def delete_user(userId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    if (current_user["userId"] == userId):
        raise HTTPException(status_code=404, detail="No self delete")

    #delete user from db
    db_user = crud_user.delete_user(db=db, userId=userId)
     
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
