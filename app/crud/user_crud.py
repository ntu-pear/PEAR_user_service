from venv import logger
from sqlalchemy.orm import Session
from sqlalchemy import update

from ..models.user_model import User

from ..schemas import user as schemas_User
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.service import user_service as UserService
from app.service import email_service as EmailService
import uuid
import cloudinary
import cloudinary.uploader

def get_user(db: Session, userId: str):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()

#Update User
async def update_user_User(db: Session, userId: str, user: schemas_User.UserUpdate_User, modified_by):
    stmt = update(User).where(User.id == userId)

    # update modified by who
    stmt = stmt.values(modifiedById=modified_by)
    for field, value in user.model_dump(exclude_unset=True).items():
        if field != "email":
            stmt = stmt.values({field: value})
        if field == "email":
            #Send confirmation email if email is changed
            email_Token = EmailService.generate_email_token(userId, value)
            await EmailService.send_confirmation_email(value, email_Token)
           

    db.execute(stmt)
    db.commit()
    # Fetch the updated user to return it
    db_user = db.query(User).filter(User.id == userId).first()
    return db_user

#Admin update other user's account
def update_user_Admin(db: Session, userId: str, user: schemas_User.UserUpdate_Admin, modified_by):
    stmt = update(User).where(User.id == userId)

    # update modified by who
    stmt = stmt.values(modifiedById=modified_by)

    if user.email:
        # Check for conflicting email before updating
        existing_user_email = db.query(User).filter(User.email == user.email).first()
        if existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )
        stmt = stmt.values(email=user.email)

    for field, value in user.model_dump(exclude_unset=True).items():
        if field != "email":
            stmt = stmt.values({field: value})

    db.execute(stmt)
    db.commit()

    # Fetch the updated user to return it
    db_user = db.query(User).filter(User.id == userId).first()
    return db_user

#Admin update selected users role
def update_users_role_admin(db: Session, userId: str, roleName: str, modified_by):
    stmt = update(User).where(User.id == userId)
    # update roleName and modified by who
    stmt = stmt.values(roleName=roleName, modifiedById=modified_by)

    db.execute(stmt)
    db.commit()

    # Fetch the updated user to return it
    db_user = db.query(User).filter(User.id == userId).first()
    return db_user

def delete_user(db: Session, userId: str):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:

        #delete user pic id from cloudinary
        if db_user.profilePicture:
            public_id = db_user.profilePicture.split("/")[-1].split(".")[0]  # Extracts `user_Ufa53ec48e2f_profile_picture`
            cloudinary.uploader.destroy(f"profile_pictures/{public_id}")
        db.delete(db_user)
        db.commit()
    return db_user

def verify_user(db: Session, user: schemas_User.UserCreate):
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

def create_user(db: Session, user: schemas_User.TempUserCreate, created_by: int):
    # Combine checks for email and NRIC into a single query
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.nric == user.nric)
    ).first()

    if existing_user:
        if existing_user.email == user.email:
            logger.error(f"Email conflict: {user.email} already exists.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )
        if existing_user.nric == user.nric:
            logger.error(f"NRIC conflict: {user.nric} already exists.")
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
    # Check ContactNo Format
    UserService.validate_contactNo(user.contactNo)
    # Check DOB Format
    UserService.validate_dob(user.nric_DateOfBirth)

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

def reset_password(db: Session, userId: str, new_password: str):
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user.password = user_auth_service.get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user

def activate_user(db: Session, userId: str):
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user.active = True
    db.commit()
    db.refresh(db_user)
    return db_user

def deactivate_user(db: Session, userId: str, lockout_reason: str, modified_by: str):
    # Fetch the user from the database
    db_user = db.query(User).filter(User.id == userId).first()
    
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Set the status to inactive and add the lockout reason
    stmt = update(User).where(User.id == userId).values(
        status="inactive",
        lockoutReason=lockout_reason,
        modifiedById=modified_by
    )

    db.execute(stmt)
    db.commit()

    # Fetch and return the updated user
    db_user = db.query(User).filter(User.id == userId).first()
    return db_user