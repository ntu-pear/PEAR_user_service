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


@router.post("/supervisor/get_doctors", response_model=schemas_user.SupervisorPaginationResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_doctor_by_name(fullName: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),page:Optional[int]=1, page_size:Optional[int]=10,db: Session = Depends(get_db)):
    is_supervisor = current_user["roleName"] == "SUPERVISOR"

    if not is_supervisor:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_doctor_supervisor(db=db, fullName=fullName, page=page,page_size=page_size)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db_user