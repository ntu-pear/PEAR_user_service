from fastapi import APIRouter, Depends, HTTPException,status, Request

from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import json
from ..database import get_db
from ..schemas import user_auth
from ..schemas.user import UserRead,UserBase
from ..models.user_model import User
from ..service import user_auth_service
from ..schemas import user_auth

# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip

router = APIRouter()

@router.post("/login/")#, response_model=user_auth.Token)
#@rate_limit_by_ip(tokens_required=1)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db),):
    # Get User
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Validate User Credentials
    if not user:
        raise user_auth_service.user_credentials_exception
    if not user_auth_service.verify_password(form_data.password, user.password):
        raise user_auth_service.user_credentials_exception
    
    # Prepare token payload
    data = {
        "userId": user.id,
        "fullName": user.nric_FullName,
        "roleName": user.roleName,
    }

    # Serialize payload and generate access token
    serialized_data = json.dumps(data)
    access_token = user_auth_service.create_access_token(data={"sub": serialized_data})
    # Return response
    return {
        "access_token": access_token,
        "token_type": "bearer",
        # Include token expiry information in the response for the client to handle reauthentication.
        "expires_in": user_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES,
        "data": data,  # Avoid sensitive data
    }

@router.get("/current_user/", response_model=user_auth.TokenData)
def read_current_user(current_access: user_auth.TokenData = Depends(user_auth_service.get_current_user)):
    return current_access
