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
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
    refresh_token = user_auth_service.create_refresh_token(data={"sub": serialized_data})
    # Return response
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        # Include token expiry information in the response for the client to handle reauthentication.
        "access_token_expires_in": user_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expires_in": user_auth_service.REFRESH_TOKEN_EXPIRE_DAYS,
        "data": data,  # Avoid sensitive data
    }
@router.post("/refresh/")
async def refresh_access_token(request: Request):
    """
    Refreshes the access token using a valid refresh token.
    The refresh token should be sent in the request body as JSON.
    """
    body = await request.json()
    refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is required")

    # Decode and validate refresh token
    payload = user_auth_service.decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Generate a new access token
    new_access_token = user_auth_service.create_access_token(
        data={
            "userId": payload["userId"], 
            "fullName": payload["fullName"], 
            "roleName": payload["roleName"]
        }
    )
    
    return {"access_token": new_access_token, "data":payload}

@router.get("/current_user/", response_model=user_auth.TokenData)
def read_current_user(current_access: user_auth.TokenData = Depends(user_auth_service.get_current_user)):
    return current_access
