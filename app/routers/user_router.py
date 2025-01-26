from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException,UploadFile, File,status
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from app.service import user_service as UserService
from app.models.user_model import User
from PIL import Image
from io import BytesIO
import logging
import os

# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip
from fastapi import Request


global_bucket = TokenBucket(rate=5, capacity=10)


router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)


# Directory to store uploaded files
UPLOAD_DIR = "uploads/profile_pictures"


# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}

#Verify Acc, add password
@router.post("/user/verify_account/", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def verify_user(token: str, user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    userDetails= EmailService.decode_access_token(token)

    db_user = crud_user.verify_user(db=db, user=user)

    return db_user

#Resend account confirmation email
@router.post("/user/request/resend_registration_email", response_model=schemas_user.UserBase)
@rate_limit(global_bucket, tokens_required=1)
async def resend_registration_email(token: str, user: schemas_account.ResendEmail, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    if (userDetails.roleName != "ADMIN"):
         raise HTTPException(status_code=404, detail="User is not authorised")
  
    #Send registration Email
    token = EmailService.generate_email_token(user.email)
    await EmailService.send_confirmation_email(user.email, token)

    return {"Message":"Email Sent"}


# Request password reset
@router.post("/user/request-reset-password/")
async def request_reset_confirmation(account: schemas_account.ResetPasswordBase, db: Session = Depends(get_db)):

    user = crud_user.get_user_by_email(db=db, email=account.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    fields_to_check = ["nric", "nric_DateOfBirth","roleName"]
    for field in fields_to_check:
        if getattr(user, field) != getattr(account, field):
            raise HTTPException(status_code=404, detail="Invalid Details")
        
    token = EmailService.generate_email_token(user.email)
    await EmailService.send_resetpassword_email(user.email, token)
  
    return {"msg": "Reset password email sent"}

@router.post("/user/reset_password/{token}")
async def reset_user_password(token: str, newPassword: str, confirmPassword: str, db: Session = Depends(get_db)):
    try:
        userDetails = EmailService.confirm_token(token) 
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if (newPassword != confirmPassword):
        raise HTTPException(status_code=404, detail="Password do not match")
    
    user = db.query(User).filter(User.email == userDetails.get("email")).first()
    #return user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = newPassword
    db.commit()
    
    return {"Password Updated"}



@router.put("/user/{userId}", response_model=schemas_user.UserUpdate)
def update_user(token:str, userId: str, user: schemas_user.UserUpdate, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)

    db_user = crud_user.update_user(db=db, userId=userId, user=user,modified_by=userDetails["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/users/upload_profile_pic/{token}")
async def upload_profile_picture(token: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    userId= userDetails["userId"]
    # Get the user from the database
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #Validate File Format
    UserService.validate_profile_picture_format(file)

    # Define the file path
    file_extension = file.filename.split(".")[-1]
    file_name = f"user_{userId}_profile_picture.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    try:
        # Read the file into memory
        contents = await file.read()

        # Open the image using Pillow
        image = Image.open(BytesIO(contents))

        # Resize the image (maintaining aspect ratio)
        max_size = (300, 300)  # Maximum width and height
        image.thumbnail(max_size)

        # Save the resized image to the target directory
        with open(file_path, "wb") as out_file:
            image.save(out_file, format=image.format)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process the image: {e}",
        )
    # Update the user's profile picture path in the database
    db_user.profilePicture = file_path
    db.commit()
    db.refresh(db_user)

    return {"message": "Profile picture uploaded successfully", "file_path": file_path}

@router.delete("/users/{userId}/delete_profile_pic/")
async def delete_profile_picture(token: str, db: Session = Depends(get_db)):
    userDetails= AuthService.decode_access_token(token)
    userId= userDetails["userId"]
    # Fetch the user from the database
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Check if the user has a profile picture
    if not db_user.profilePicture:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture found for this user.",
        )

    # Get the file path
    file_path = db_user.profilePicture

    try:
        # Delete the file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile picture file not found on the server.",
            )

        # Update the database
        db_user.profilePicture = None
        db.commit()

        return {"message": "Profile picture deleted successfully."}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the profile picture: {e}",
        )