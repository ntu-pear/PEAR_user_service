from app.utils.utils import mask_nric
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
    tags=["admin"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}

#Create Acc, unverified
@router.post("/admin/create_account/", response_model=schemas_user.UserRead)
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



@router.get("/admin/{userId}", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
def read_user(token: str, userId: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mask NRIC if the token's user ID does not match the requested user's ID or requested user not admin
    if userDetails["userId"] != userId or userDetails["roleName"] != "ADMIN":
        db_user.nric = mask_nric(db_user.nric)
   
    return db_user

@router.get("/admin/", response_model=list[schemas_user.UserRead])
@rate_limit(global_bucket, tokens_required=1)
def read_users(token: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    # if token exists and user is admin, then do not need to mask NRICs
    if token:
        try:
            userDetails = AuthService.decode_access_token(token)
            is_admin = userDetails.get("roleName") == "ADMIN"
        except Exception:
            # If token is invalid, treat as no token
            is_admin = False
    else:
        is_admin = False

    # otherwise by default, mask all NRICs
    if not is_admin:
        for user in users:
            user.nric = mask_nric(user.nric)

    return users

@router.get("/admin/get_email/{email}", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def get_user_by_email(token:str, email: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/admin/{userId}", response_model=schemas_user.UserUpdate)
def update_user_by_admin(token:str, userId: str, user: schemas_user.UserUpdate_Admin, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    db_user = crud_user.update_user(db=db, userId=userId, user=user,modified_by=userDetails["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/admin/{userId}", response_model=schemas_user.UserBase)
def delete_user(token: str, userId: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    if (userDetails["roleName"] != "ADMIN"):
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.delete_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
