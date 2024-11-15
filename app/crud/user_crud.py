from sqlalchemy.orm import Session
from ..models.user_model import User
from ..schemas.user import UserCreate, UserUpdate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

def get_user(db: Session, userId: int):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
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
    # Check if the username is already registered
    existing_user_username = db.query(User).filter(User.userName == user.userName).first()
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists."
        )

    # Use a transaction to ensure rollback on error
    try:
        # Hashes the password
        user.passwordHash = user_auth_service.get_password_hash(user.passwordHash)
        db_user = User(**user.dict())
        
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


def update_user(db: Session, userId: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        for key, value in user.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, userId: int):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
