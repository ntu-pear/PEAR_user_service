from venv import logger
from sqlalchemy.orm import Session
from sqlalchemy import update

from ..models.user_model import User
import json
from ..schemas import user as schemas_User
from ..service import user_auth_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.service import user_service as UserService
from app.service import email_service as EmailService
from app.service import user_auth_service as AuthService


#create session and return access & refresh token
def create_session(user, db:Session = Depends(get_db)):
    # Create session
    
    # Generate and return token
    return AuthService.return_tokens(user)

   
#Update session


#Delete session