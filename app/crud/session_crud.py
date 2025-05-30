from venv import logger
from sqlalchemy.orm import Session
import pytz  # Import pytz for timezone conversion
from sqlalchemy import update, DateTime
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from ..models.user_model import User
from ..models.session_model import User_Session
import json
from ..schemas import user as schemas_User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.service import user_auth_service as AuthService
import uuid
import os
# Setup Variables
SESSION_EXPIRY_MINUTES=int(os.getenv("SESSION_EXPIRE_MINUTES", "0"))
# Set timezone to Singapore Time (SGT)
sgt_tz = pytz.timezone("Asia/Singapore")

#create session and return access & refresh token
def create_session(user, db:Session = Depends(get_db)):
    # Create session
    # Generate a unique ID with a fixed length of 20
    while True:
        unique_id = uuid.uuid4().hex[:20]
        # Ensure the total length is 11 characters
        sessionId =unique_id[:20]  # Truncate to 20 if necessary
        existing_session_id = db.query(User_Session).filter(User_Session.id == sessionId).first()
        if not existing_session_id:
            break
    #Create tokens
    userTokens = AuthService.create_tokens(user,sessionId)
    #Commit to DB
    # Use a transaction to ensure rollback on error
    # Add 2 days to the current timestamp for expiry
    #expiry_timestamp = datetime.now() + timedelta(days=2)

    # Set timezone to Singapore (SGT = UTC+8)
    expiry_timestamp = datetime.now(sgt_tz) + timedelta(minutes=SESSION_EXPIRY_MINUTES)  # Expire in 10 min

    #Check for any other sessions, if yes delete them
    delete_user_sessions(userId=user.id, db=db)

    try:
        db_session = User_Session(id=sessionId,user_id=user.id, access_Token=userTokens["access_token"], refresh_Token=userTokens["refresh_token"], expired_at=expiry_timestamp)
        # Begin transaction
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    except IntegrityError as e:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        print(e.orig)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a duplicate unique field."
        )

    # Generate and return token
    return userTokens

   
#Update session, update new access token
def update_session(session_id: str,access_Token:str, db: Session = Depends(get_db)):
    # Find session in DB
    db_session = db.query(User_Session).filter(User_Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Ensure `expired_at` is timezone-aware
    if db_session.expired_at.tzinfo is None:
        expired_at_aware = db_session.expired_at.replace(tzinfo=pytz.utc)  # Assume stored in UTC
    else:
        expired_at_aware = db_session.expired_at
    # Set timezone to Singapore Time (SGT)
    current_timestamp = datetime.now(sgt_tz)  # Get current time in SGT
    #Check if session is expired
    if expired_at_aware < current_timestamp:
        db.delete(db_session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    
    #update new access_token
    db_session.access_Token=access_Token
    db.commit()

#Delete Sessions associated to User
def delete_user_sessions(userId: str, db:Session=Depends(get_db)):
    db_user_sessions = db.query(User_Session).filter(User_Session.user_id==userId).all()
    if db_user_sessions:
        for session in db_user_sessions:
            delete_session(session_id=session.id, db=db)
        return True
    return False

#Delete sessions
def delete_sessions(db: Session = Depends(get_db)):
    # Find session in DB
    db_session = db.query(User_Session).all()
    #loop thru all the sessions
    for session in db_session:
        check_session_expiry(session_id=session.id, db=db)


#Delete 1 session
def delete_session(session_id: str, db: Session = Depends(get_db)):
    # Find session in DB
    db_session = db.query(User_Session).filter(User_Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    #delete Session
    db.delete(db_session)
    db.commit()


#Get Session
def get_session(session_id: str, db: Session = Depends(get_db)):
    # Find session in DB
    db_session = db.query(User_Session).filter(User_Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

#Check if session has expired
def check_session_expiry(session_id: str, db: Session = Depends(get_db)):
    # Find session in DB
    db_session = db.query(User_Session).filter(User_Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Ensure `expired_at` is timezone-aware
    if db_session.expired_at.tzinfo is None:
        expired_at_aware = db_session.expired_at.replace(tzinfo=pytz.utc)  # Assume stored in UTC
    else:
        expired_at_aware = db_session.expired_at
    # Set timezone to Singapore Time (SGT)
    current_timestamp = datetime.now(sgt_tz)  # Get current time in SGT
    #Check if session is expired
    if expired_at_aware < current_timestamp:
        db.delete(db_session)
        db.commit()
        return True
    
    return False
