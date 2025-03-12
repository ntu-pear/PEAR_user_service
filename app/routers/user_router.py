from app.schemas import user_auth
from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException,UploadFile, File,status,Security
from fastapi.responses import FileResponse 
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from app.service import validation_service as Validation_Service
from app.models.user_model import User
from sqlalchemy.exc import IntegrityError
import cloudinary
import cloudinary.uploader
from PIL import Image
from io import BytesIO
import pytz  # Import pytz for timezone conversion
from datetime import datetime
# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit, rate_limit_by_ip
from fastapi import Request

# import cache
from cachetools import TTLCache
# import cache and event listener
from sqlalchemy import event
from cachetools import TTLCache



sgt_tz = pytz.timezone("Asia/Singapore")
global_bucket = TokenBucket(rate=5, capacity=10)

# Create a cache for user details (maxsize=100, TTL=300 seconds)
user_cache = TTLCache(maxsize=100, ttl=300)

# Create a cache for user details (maxsize=100, TTL=300 seconds)
user_cache = TTLCache(maxsize=100, ttl=300)


router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)


# Profile Picture Max Size
MAX_SIZE = (300, 300)  # Max image size (300x300)

# Retrieve User from cache
def get_cached_user(user_id: int, db: Session):
    if user_id in user_cache:
        return user_cache[user_id]
    
    # otherwise fetch from DB
    db_user = crud_user.get_user(db=db, userId=user_id)
    if db_user:
        user_cache[user_id] = db_user
    return db_user
# Retrieve User from cache
def get_cached_user(user_id: int, db: Session):
    if user_id in user_cache:
        return user_cache[user_id]
    
    # otherwise fetch from DB
    db_user = crud_user.get_user(db=db, userId=user_id)
    if db_user:
        user_cache[user_id] = db_user
    return db_user

# invalidate cache and update it with latest data
def update_user_cache(user_id: int, updated_user_data):
    user_cache[user_id] = updated_user_data

# Remove user from cache when deleted
def remove_user_from_cache(user_id: int):
    user_cache.pop(user_id, None)

# **🔵 SQLAlchemy Event Listeners for Auto Cache Refresh**
# mapper: Represents the ORM mapping of the model class (User in this case).
# connection: Represents the active database connection, allowing direct execution of SQL queries if necessary.
# target: The actual instance of the model being modified.
def refresh_cache(_mapper, _connection, target):
    """Auto-refresh cache when a user is modified."""
    update_user_cache(target.id, target)

def remove_cache(_mapper, _connection, target):
    """Remove user from cache when deleted."""
    remove_user_from_cache(target.id)

# **Attach event listeners to User model**
event.listen(User, "after_update", refresh_cache)  # Update cache on change
event.listen(User, "after_insert", refresh_cache)  # Insert user into cache
event.listen(User, "after_delete", remove_cache)   # Remove from cache on delete

# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}

#Verify Acc, add password
@router.post("/user/verify_account/{token}", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
async def verify_user(token: str, user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    try:
        userDetails = EmailService.confirm_token(token) 
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db_user = db.query(User).filter(User.email == userDetails.get("email")).first()
    #return user
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user = crud_user.verify_user(db=db, user=user)
    return db_user

#fetch user details (Cached) (Cached)
@router.get("/user/get_user/", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
def read_user(current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    userId = current_user["userId"]
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return schemas_user.UserRead.from_orm(db_user)

#Change Password
@router.put("/user/change_password/")
@rate_limit(global_bucket, tokens_required=1)
def user_change_password(password:schemas_account.UserChangePassword,current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    userId = current_user["userId"]
    # Get User
    user = db.query(User).filter(User.id == userId).first()
    # verify current password
    if not AuthService.verify_password(password.currentPassword, user.password):
        raise AuthService.user_credentials_exception
    if (password.newPassword != password.confirmPassword):
        raise HTTPException(status_code=404, detail="Password do not match")
    try:
        #Check password format
        Validation_Service.validate_password_format(password.newPassword)
        #Hash password
        user.password = AuthService.get_password_hash(password.newPassword)
        #update modifiedById
        user.modifiedById=user.id
        #upadte last password changed time stamp
        user.lastPasswordChanged=datetime.now(sgt_tz)
        db.commit()
    except IntegrityError:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a wrong password format."
        )
    return {"Password Updated"}

#Change Email
@router.put("/user/confirm_email/{token}")
@rate_limit(global_bucket, tokens_required=1)
def user_change_email(token: str, db: Session = Depends(get_db)):
    try:
        userDetails = EmailService.confirm_token(token) 
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.id == userDetails.get("userId")).first()
    #return user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #Change to new email
    user.email = userDetails.get("email")
    db.commit()
    return {"Email Updated"}


#Resend account confirmation email
@router.post("/user/request/resend_registration_email") 
@rate_limit(global_bucket, tokens_required=1)
async def resend_registration_email(account: schemas_account.ResendEmail, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db=db, email=account.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    #check if user is already verified
    if user.verified:
        raise HTTPException(status_code=404, detail="User is already verified")
    
    fields_to_check = ["nric", "nric_DateOfBirth","email", "roleName"]
    for field in fields_to_check:
        if getattr(user, field) != getattr(account, field):
            raise HTTPException(status_code=404, detail="Invalid Details")
  
    #Send registration Email
    token = EmailService.generate_email_token(user.id, user.email)
    await EmailService.send_registration_email(user.email, token)

    return {"Message":"Registration Email Sent"}


# Request password reset
@router.post("/user/request_reset_password/")
async def request_reset_password(account: schemas_account.RequestResetPasswordBase, db: Session = Depends(get_db)):

    user = crud_user.get_user_by_email(db=db, email=account.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    fields_to_check = ["nric", "nric_DateOfBirth","email", "roleName"]
    for field in fields_to_check:
        if getattr(user, field) != getattr(account, field):
            raise HTTPException(status_code=404, detail="Invalid Details")
        
    token = EmailService.generate_email_token(user.id, user.email)
    await EmailService.send_reset_password_email(user.email, token)
  
    return {"msg": "Reset password email sent"}

#Change password
@router.put("/user/reset_user_password/{token}")
async def reset_user_password(token: str, userResetPassword: schemas_account.UserResetPassword , db: Session = Depends(get_db)):
    try:
        userDetails = EmailService.confirm_token(token) 
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if (userResetPassword.newPassword != userResetPassword.confirmPassword):
        raise HTTPException(status_code=404, detail="Password do not match")
    
    user = db.query(User).filter(User.email == userDetails.get("email")).first()
    #return user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        #Check password format
        Validation_Service.validate_password_format(userResetPassword.newPassword)
        #Hash password
        user.password = AuthService.get_password_hash(userResetPassword.newPassword)
        #update modifiedById
        user.modifiedById=user.id
        #update last password changed time stamp
        user.lastPasswordChanged=datetime.now(sgt_tz)
        db.commit()
    except IntegrityError:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a wrong password format."
        )
    return {"Password Updated"}

#update user
@router.put("/user/update_user/", response_model=schemas_user.UserRead)
async def update_user(user: schemas_user.UserUpdate_User, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    userId = current_user["userId"]
    db_user = await crud_user.update_user_User(db=db, userId=userId, user=user,modified_by=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/user/upload_profile_pic/")
async def upload_profile_picture(file: UploadFile = File(...),current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    #Get current user Id
    user_id = current_user["userId"]
    #Fetch user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Validate file type
    Validation_Service.validate_profile_picture_format(file)

    try:
        # # Delete old profile picture from Cloudinary**
        if db_user.profilePicture:
            old_public_id = db_user.profilePicture.split("/")[-1].split(".")[0]  # Extract public ID
            cloudinary.uploader.destroy(f"profile_pictures/{old_public_id}")

        # Open the image
        image = Image.open(BytesIO(await file.read()))

        # Resize the image (maintains aspect ratio)
        image.thumbnail(MAX_SIZE)

        # Save to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        # Upload to Cloudinary
        upload_response = cloudinary.uploader.upload(
            buffer,
            folder="profile_pictures",
            public_id=f"user_{user_id}_profile_picture",
            overwrite=True
        )

        # Get the uploaded image URL
        image_url = upload_response.get("secure_url")
        # Update ModifiedById
        db_user.modifiedById = db_user.id
        
        db_user.profilePicture = image_url
        db.commit()
        db.refresh(db_user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

    return {"message": "Profile picture uploaded successfully", "file_url": db_user.profilePicture}

@router.get("/user/profile_pic/")
async def get_profile_picture(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    #Get current user Id
    user_id = current_user["userId"]

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.profilePicture:
        raise HTTPException(status_code=404, detail="Profile picture not found")

    return {"image_url": db_user.profilePicture}

@router.delete("/user/delete_profile_pic/")
async def delete_profile_picture(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    #Get current user Id
    user_id = current_user["userId"]

    # Fetch user from DB
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.profilePicture:
        raise HTTPException(status_code=404, detail="No profile picture found.")

    # Extract Cloudinary public_id from image URL
    try:
        public_id = db_user.profilePicture.split("/")[-1].split(".")[0]  # Extracts `user_Ufa53ec48e2f_profile_picture`
        cloudinary.uploader.destroy(f"profile_pictures/{public_id}")

        # Remove profile picture reference from DB
        db_user.profilePicture = None
        # Update ModifiedById
        db_user.modifiedById = db_user.id

        db.commit()
        db.refresh(db_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting profile picture: {str(e)}")

    return {"message": "Profile picture deleted successfully"}