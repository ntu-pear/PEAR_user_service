from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from app.models.user_model import User
import logging
import sys

# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit

global_bucket = TokenBucket(rate=5, capacity=10)


router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)
#Create Acc, unverified
@router.post("/users/create_account/", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def create_user(token: str, user: schemas_user.TempUserCreate, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
   
    if (userDetails["roleName"] != "ADMIN"):
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user=crud_user.create_user(db=db, user=user, created_by=userDetails["userId"])
    if db_user:
        #Send registration email
        token = EmailService.generate_email_token(user.email)
        await EmailService.send_registration_email(user.email, token)
   
    return db_user

#Verify Acc, add password
@router.post("/users/verify_account/", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def verify_user(token: str, user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    userDetails= EmailService.decode_access_token(token)

    db_user = crud_user.verify_user(db=db, user=user)

    return db_user

#Resend account confirmation email
@router.post("/users/request/resend_registration_email", response_model=schemas_user.UserBase)
@rate_limit(global_bucket, tokens_required=1)
async def resend_registration_email(token: str, user: schemas_account.ResendEmail, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    if (userDetails.roleName != "ADMIN"):
         raise HTTPException(status_code=404, detail="User is not authorised")
  
    #Send registration Email
    token = EmailService.generate_email_token(user.email)
    await EmailService.send_confirmation_email(user.email, token)

    return {"Message":"Email Sent"}

@router.get("/users/{userId}", response_model=schemas_user.UserRead)
def read_user(token: str, userId: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/users/", response_model=list[schemas_user.UserRead])
@rate_limit(global_bucket, tokens_required=1)
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/users/get_email/{email}", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def get_user_by_email(token:str, email: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{userId}", response_model=schemas_user.UserUpdate)
def update_user(token:str, userId: str, user: schemas_user.UserUpdate, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.update_user(db=db, userId=userId, user=user,modified_by=userDetails["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/users/{userId}", response_model=schemas_user.UserBase)
def delete_user(token: str, userId: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    if (userDetails["roleName"] != "ADMIN"):
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.delete_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

