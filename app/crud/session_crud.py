from venv import logger
from sqlalchemy.orm import Session
from sqlalchemy import update, DateTime
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from ..models.user_model import User
from ..models.session_model import User_Session
import json
from ..schemas import user as schemas_User
from ..service import user_auth_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.service import user_service as UserService
from app.service import email_service as EmailService
from app.service import user_auth_service as AuthService
import uuid

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
    #test
    expiry_timestamp = datetime.now() + timedelta(minutes=10)
    try:
        db_session = User_Session(id=sessionId, access_Token=userTokens["access_token"], refresh_Token=userTokens["refresh_token"], expired_at=expiry_timestamp)
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
    # Get current timestamp using datetime.now()
    current_timestamp = datetime.now()
    #Check if session is expired
    if db_session.expires_at < current_timestamp:
        db.delete(db_session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    
    #update new access_token
    db_session.access_Token=access_Token
    db.commit()

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
    current_timestamp = datetime.now()
    #Check if session is expired
    if db_session.expired_at < current_timestamp:
        db.delete(db_session)
        db.commit()
        return True
    
    return False
