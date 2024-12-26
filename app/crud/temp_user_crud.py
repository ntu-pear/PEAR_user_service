from sqlalchemy.orm import Session
from ..models.temp_user_model import Temp_User
from ..schemas.temp_user import CreateTempUser, ReadTempUser, UpdateTempUser

from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.service.common_service import validate_nric


def get_temp_user(db: Session, userId: int):
    return db.query(Temp_User).filter(Temp_User.id == userId).first()

def get_temp_user_by_email(db: Session, email: str):
    return db.query(Temp_User).filter(Temp_User.email == email).first()

def get_temp_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Temp_User).order_by(Temp_User.id).offset(skip).limit(limit).all()

def create_temp_user(db: Session, user: CreateTempUser):
    # Check if the email is already registered
    existing_temp_user_email = db.query(Temp_User).filter(Temp_User.email == user.email).first()
    if existing_temp_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    # Check if the nric is already registered
    existing_user_nric = db.query(Temp_User).filter(Temp_User.nric == user.nric).first()
    if existing_user_nric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this nric already exists."
        )
    if not validate_nric(user.nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC Format."
        )
    # Use a transaction to ensure rollback on error
    try:
        db_user = Temp_User(**user.dict())
        
        # Begin transaction
        db.add(db_user)
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


def update_temp_user(db: Session, userId: int, user: UpdateTempUser):
    db_user = db.query(Temp_User).filter(Temp_User.id == userId).first()
    if db_user:
        for key, value in user.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_temp_user(db: Session, userId: int):
    db_user = db.query(Temp_User).filter(Temp_User.id == userId).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
