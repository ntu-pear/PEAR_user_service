from sqlalchemy.orm import Session
from ..models.user_model import User
from ..models.temp_user_model import Temp_User
from ..schemas.user import UserCreate, UserUpdate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from ..crud import user_role_crud as crud_role_user
from app.service.common_service import validate_nric


def get_user(db: Session, userId: int):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()

def update_user(db: Session, userId: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        for key, value in user.dict().items():
            #check if value is not empty
            if value is not "":
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, userId: int):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        #delete all user role associated with user
        crud_role_user.delete_user_role_userId(db, db_user.id)
        db.delete(db_user)
        db.commit()
    return db_user

def create_user(db: Session, user: UserCreate):
    #Verify Info with Temp User DB
    temp_user= db.query(Temp_User).filter(Temp_User.email == user.email).first()
    if not verify_temp_user(temp_user, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Details do not match with pre-registered details"
    )
        
    # Check if the email is already registered
    existing_user_email = db.query(User).filter(User.email == user.email).first()
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Check if the nric is already registered
    existing_user_nric = db.query(User).filter(User.nric == user.nric).first()
    if existing_user_nric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this nric already exists."
        )
    #dont need to validate nric, since temp crud already validated
    if not validate_nric(user.nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC Format."
        )

    # Use a transaction to ensure rollback on error
    try:
        # Hashes the password
        user.passwordHash = user_auth_service.get_password_hash(user.passwordHash)
        db_user = User(**user.dict())
        
        # Begin transaction
        db.add(db_user) #Add new user to DB
        db. delete(temp_user) #Delete temp user from DB
        db.commit()
        db.refresh(db_user)

    except IntegrityError:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a duplicate unique field."
        )

    return db_user

def verify_temp_user(temp_user, user):
    # Define the fields to compare
    fields_to_check = ["nric", "email", "dateOfBirth", "contactNo", "role"]
    for field in fields_to_check:
        if getattr(temp_user, field) != getattr(user, field):
            return False
    return True
