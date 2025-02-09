from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.crud.role_crud import get_role
from ..models.user_model import User
from ..database import get_db
import os
import logging
import json

# Setup Variables
SECRET_KEY=os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = "FakeKey"
    logging.warning("SECRET_KEY environment variable not set. Using an insecure fallback for development.")
    # raise ValueError("SECRET_KEY environment variable not set.")
REFRESH_SECRET_KEY=os.getenv('REFRESH_SECRET_KEY')
if not REFRESH_SECRET_KEY:
    SECRET_KEY = "FakeKey2"
    logging.warning("REFRESH_SECRET_KEY environment variable not set. Using an insecure fallback for development.")
    # raise ValueError("SECRET_KEY environment variable not set.")


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) # Token validity period
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")) # Token validity period
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# Errors
missing_field_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token is missing 'sub' claim field from JWT Token payload",
    headers={"WWW-Authenticate": "Bearer"},
)

expired_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)

invalid_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, 
    detail="Could not validate token"
)

unknown_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unexpected error decoding token. Please provide a valid token.",
)

user_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials of user",
    headers={"WWW-Authenticate": "Bearer"},
)


# Methods
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    # extracts user details from jwt token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_details = json.loads(payload.get("sub"))
        if not user_details:
            raise missing_field_exception
        return user_details
    # deal with invalid token/expired token
    except JWTError as e:
        if "Signature has expired" in str(e):
            raise expired_token_exception
        else:
            raise invalid_token_exception
    # deal with else case for errors
    except Exception as e:
        logging.error(f"Unexpected token decoding error: {e}")
        raise unknown_token_exception

def decode_refresh_token(token: str):
    # extracts user details from jwt token
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_details = json.loads(payload.get("sub"))
        if not user_details:
            raise missing_field_exception
        return user_details
    # deal with invalid token/expired token
    except JWTError as e:
        if "Signature has expired" in str(e):
            raise expired_token_exception
        else:
            raise invalid_token_exception
    # deal with else case for errors
    except Exception as e:
        logging.error(f"Unexpected token decoding error: {e}")
        raise unknown_token_exception

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # get user details from access token
    userDetails = decode_access_token(token)
    user = db.query(User).filter(User.id == userDetails["userId"]).first()

    if not user:
        raise user_credentials_exception

    return {"userId": user.id, "fullName": user.nric_FullName, "roleName": user.roleName}