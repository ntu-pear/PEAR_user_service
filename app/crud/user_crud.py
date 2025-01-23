from sqlalchemy.orm import Session
from ..models.user_model import User

from ..schemas.user import UserCreate, UserUpdate, TempUserCreate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from ..crud import user_role_crud as crud_role_user
from app.service import user_service as UserService
import uuid


def get_user(db: Session, userId: str):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()
#get user by on field
def get_user_by_field(db: Session, field:str, input: str):
    return db.query(User).filter(User.field == input).first()

def update_user(db: Session, userId: str, user: UserUpdate, modified_by):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        #Update modified by Who
        db_user.modifiedById = modified_by
        # Update only provided fields
        for field, value in user.model_dump(exclude_unset=True).items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, userId: str):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def verify_user(db: Session, user: UserCreate):
    #Verify Info with User DB
    db_user= db.query(User).filter(User.email == user.email).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if db_user.verified == False:
        if not UserService.verify_userDetails(db_user, user):
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
        #Check password format
        UserService.validate_password_format(user.password)
        # Hashes the password
        db_user.password = user_auth_service.get_password_hash(user.password)
        #Set Account as Verified
        db_user.verified = True
        
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

def create_user(db: Session, user: TempUserCreate, created_by: int):
    
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
    
    # Generate a unique ID with a fixed length of 11
    while True:
        unique_id = "U" + str(uuid.uuid4().hex[:10])
        # Ensure the total length is 11 characters
        userId =unique_id[:10]  # Truncate to 11 if necessary
        existing_user_id = db.query(User).filter(User.id == userId).first()
        if not existing_user_id:
            break

    # Check NRIC Format
    UserService.validate_nric(user.nric)
    
    # Use a transaction to ensure rollback on error
    try:
        db_user = User(**user.model_dump(), createdById = created_by, modifiedById= created_by, id=userId)

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

