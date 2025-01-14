from sqlalchemy.orm import Session
from ..models.user_model import User

from ..schemas.user import UserCreate, UserUpdate, TempUserCreate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from ..crud import user_role_crud as crud_role_user
from app.service.common_service import validate_nric
import uuid

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
            if value != "":
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

def verify_user(db: Session, user: UserCreate):
    #Verify Info with User DB
    db_user= db.query(User).filter(User.email == user.email).first()
    if db_user.verified == "N":
        if not verify_userDetails(db_user, user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Details do not match with pre-registered details"
    ) 
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has already been verified"
        )

    # Use a transaction to ensure rollback on error
    try:
        # Hashes the password
        db_user.passwordHash = user_auth_service.get_password_hash(user.passwordHash)
        db_user.verified = "Y"
        
        # Begin transaction
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

def create_user(db: Session, user: TempUserCreate):
    # Generate unique ID
    while True:
        user.id = str(uuid.uuid4())
        existing_user_id = db.query(User).filter(User.id == user.id).first()
        if not existing_user_id:
            break
    # Check NRIC Format
    if not validate_nric(user.nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC Format."
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
    # Use a transaction to ensure rollback on error
    try:
        db_user = User(**user.dict())
        
        # Begin transaction
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    except IntegrityError as e:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        print(e.orig)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a duplicate unique field."
        )

    return db_user

def super_create_user(db: Session, user: TempUserCreate):
    # Check NRIC Format
    if not validate_nric(user.nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC Format."
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
    # Use a transaction to ensure rollback on error
    try:
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

def verify_userDetails(db_user, user):
    # Define the fields to compare
    fields_to_check = ["nric_FullName","nric", "email", "nric_DateOfBirth", "contactNo", "roleName"]
    for field in fields_to_check:
        if getattr(db_user, field) != getattr(user, field):
            return False
    return True