from fastapi import APIRouter, Depends, HTTPException,status, Request

from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import json
from fastapi.security import OAuth2PasswordBearer
import pytz  # Import pytz for timezone conversion
from datetime import datetime
from ..database import get_db
from ..schemas import user_auth
from ..models.user_model import User
from ..service import user_auth_service
from ..schemas import user_auth
from ..routers import verification_router as verification
from ..crud import session_crud as user_Session
import os
# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip
sgt_tz = pytz.timezone("Asia/Singapore")
router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES" , "0")) # Token validity period
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

@router.post("/login/")#, response_model=user_auth.Token)
#@rate_limit_by_ip(tokens_required=1)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Get User
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check is user is verified
    if not user or not user_auth_service.verify_password(form_data.password, user.password):
        raise user_auth_service.user_credentials_exception
    if not user.verified:
        raise user_auth_service.user_verify_exception
    
    #check is user enabled 2FA
    if user.twoFactorEnabled:
        await verification.request_otp(user.email, db)  # Send OTP email
        return {"msg": "2FA required", "email": user.email}  # Prompt to enter OTP
    
    #Update Login Time stamp
    user.loginTimeStamp = datetime.now(sgt_tz)
    db.commit()
    # If 2FA is not enabled, proceed to create session, generate and return tokens
    return user_Session.create_session(user, db)

@router.post("/refresh/")
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
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
    
    data={
            "userId": payload["userId"], 
            "fullName": payload["fullName"], 
            "roleName": payload["roleName"],
            "email": payload["email"]
        }
    #hide session id from frontend
    serialized_data = json.dumps({**data, "sessionId": payload["sessionId"]})
    # Generate a new access token
    new_access_token = user_auth_service.create_access_token(data={"sub": serialized_data})
    #check if refresh mapped to session
    user_auth_service.check_refresh_token(session_id=payload["sessionId"], token=refresh_token, db=db)
    #update session
    user_Session.update_session(session_id=payload["sessionId"],access_Token= new_access_token["token"],db=db)
    
    return {
        "access_token": new_access_token["token"],
        "refresh_token": refresh_token,
        "token_type": "bearer",
        # Include token expiry information in the response for the client to handle reauthentication.
        "access_token_expires_at":new_access_token["expires_at"],
        "server_time": datetime.now(sgt_tz)
        #"data": data,  # Avoid sensitive data
    }

@router.delete("/logout/")
def logout_user(access_token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    token = user_auth_service.decode_access_token(access_token)
    user_id = token["userId"]
    logout= user_Session.delete_user_sessions(userId=user_id, db=db)
    if logout:
        return {"msg":"Successful Log Out"}
    return{"msg":"Invalid User"}
    

@router.get("/current_user/", response_model=user_auth.TokenData)
def read_current_user(current_access: user_auth.TokenData = Depends(user_auth_service.get_current_user)):
    return current_access
