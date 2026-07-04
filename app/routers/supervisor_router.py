from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user 
from ..crud import role_crud as crud_role
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..schemas import user_auth
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from ..service.service_auth import verify_service_api_key, get_optional_current_user
from app.models.user_model import User
import logging
import sys
import os
from typing import Optional


# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit

global_bucket = TokenBucket(rate=5, capacity=10)

router = APIRouter(
    tags=["supervisor"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}


@router.post("/supervisor/get_doctor")
@rate_limit(global_bucket, tokens_required=1)
def get_doctor_by_name(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_supervisor = current_user["roleName"] == "SUPERVISOR"

    if not is_supervisor:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user=db.query(User).filter((User.roleName=="DOCTOR")&(User.id == userId)).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db_user.nric_FullName

@router.get("/supervisor/get_active_staff", response_model=schemas_user.UserRoleListResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_active_staff(
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user),
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
):
    is_supervisor = current_user and current_user.get("roleName") == "SUPERVISOR"
    is_service = x_api_key and x_api_key == os.environ.get("INTERNAL_SERVICE_API_KEY")

    if not is_supervisor and not is_service:
        raise HTTPException(status_code=403, detail="Not authorised")

    role_whitelist = ["DOCTOR", "SUPERVISOR", "GAME THERAPIST", "CAREGIVER"]
    db_users=db.query(User).filter((User.roleName.in_(role_whitelist))&(User.isDeleted==False)).all()
    result = []
    for user in db_users:
        user_data = schemas_user.UserRoleWithName(
            id=user.id,
            role=user.roleName,
            nric_FullName=user.nric_FullName
        )
        result.append(user_data)
    return schemas_user.UserRoleListResponse(users=result)