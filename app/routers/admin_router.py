from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user 
from ..crud import role_crud as crud_role
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
from typing import Optional

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

@router.get("/admin/{userId}", response_model=schemas_user.AdminRead.from_orm)
@rate_limit(global_bucket, tokens_required=1)
def get_user_by_id(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.get("/admin/get_nric/{userId}")
@rate_limit(global_bucket, tokens_required=1)
def get_user_nric(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user.nric

@router.post("/admin/get_users_by_fields", response_model=schemas_user.UserPaginationResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_users_by_fields(fields: schemas_user.AdminSearch, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),page:Optional[int]=1, page_size:Optional[int]=10,db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_users_by_fields(db=db, fields=fields, page=page,page_size=page_size)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db_user


@router.get("/admin/get_guardian/{nric}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
def read_guadrian_nric(nric: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_guardian_nric(db=db, nric=nric)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.get("/admin/", response_model=schemas_user.UserPaginationResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_all_users(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), page: Optional[int]= 1, page_size:Optional[int]=10, db: Session = Depends(get_db)):
    
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    #Only Admin can read all users
    users = crud_user.get_users(db=db, page=page,page_size=page_size)

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

@router.put("/admin/{userId}", response_model=schemas_user.AdminRead)
def update_user_by_admin(userId: str, user: schemas_user.UserUpdate_Admin,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.update_user_Admin(db=db, userId=userId, user=user,modified_by=current_user["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/admin/reset_and_update_users_role/")
def reset_and_update_users_role(request: schemas_user.UpdateUsersRoleRequest,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    updated_users = []
    failed_updates=[]
    update_list = request.users_Id
    db_users= crud_role.get_users_by_role(role_name=request.role, db=db)
    #No updates for admin role
    if request.role != "ADMIN":
        for user in db_users:
            if user["id"] in update_list:
                #remove user from update list
                update_list.remove(user["id"])
            else:
                #cannot remove admin
                if request.role != "ADMIN":
                    #remove user's role
                    db_user=crud_user.update_users_role_admin(db=db, userId = user["id"], roleName= None,modified_by=current_user["userId"])
                    if db_user:
                        updated_users.append({"users_id": db_user.id, "FullName":db_user.nric_FullName, "role": db_user.roleName})

        for userId in update_list:
            db_user=crud_user.update_users_role_admin(db=db, userId=userId, roleName=request.role,modified_by=current_user["userId"])
            if db_user:
                updated_users.append({"users_id": db_user.id, "FullName":db_user.nric_FullName, "role": db_user.roleName})
            if db_user is None:
                failed_updates.append({"users_id": userId, "error": "User not found"})
    return {"Updated Users": updated_users, "Failed Updates":failed_updates}

@router.delete("/admin/{userId}", response_model=schemas_user.AdminRead)
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


