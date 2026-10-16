from app.schemas import user_auth
from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException,UploadFile, File,status,Security
from fastapi.responses import FileResponse 
from sqlalchemy.orm import Session

from ..crud.user_crud import get_changed_fields
from ..database import get_db
from ..crud import user_crud as crud_user
from ..logger.logger_utils import log_crud_action, ActionType
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
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
import logging

logger = logging.getLogger(__name__)


sgt_tz = pytz.timezone("Asia/Singapore")
global_bucket = TokenBucket(rate=5, capacity=10)
# use this global bucket to test rate limiter, to make it run out of tokens
# global_bucket = TokenBucket(rate=0.1, capacity=10)

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

#fetch user details (Cached) (Cached)
@router.get("/user/get_user/", response_model=schemas_user.UserRead)
@rate_limit(global_bucket, tokens_required=1)
def read_user(current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    userId = current_user["userId"]
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas_user.UserRead.from_orm(db_user)

@router.get("/user/username/{user_id}", response_model=schemas_user.UsernameResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_username_by_id(
    user_id: str,
    _current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    result = crud_user.get_user(db=db, userId=user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas_user.UsernameResponse(
        id=result.id,
        preferredName=result.preferredName,
        nric_FullName=result.nric_FullName
    )

# Batch id -> display name lookup (used by the logging service). Deliberately not
# behind the global rate-limit bucket: one page of logs would exhaust it app-wide.
@router.post("/user/names", response_model=schemas_user.UserNamesResponse)
def get_usernames_by_ids(
    body: schemas_user.UserNamesRequest,
    _current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    if str((_current_user or {}).get("roleName", "")).upper() == "GUARDIAN":
        raise HTTPException(status_code=403, detail="Not permitted")
    ids = list(dict.fromkeys(body.ids))
    rows = db.query(User).filter(User.id.in_(ids)).all()
    names = {}
    for row in rows:
        name = row.nric_FullName or row.preferredName
        if name:
            names[row.id] = name
    return schemas_user.UserNamesResponse(names=names)

#Change Password
@router.put("/user/change_password/")
@rate_limit(global_bucket, tokens_required=1)
def user_change_password(password:schemas_account.UserChangePassword,current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    userId = current_user["userId"]
    userName = current_user["fullName"]
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
        #update last password changed time stamp
        user.lastPasswordChanged=datetime.now(sgt_tz)
        db.commit()

        logger.info(f"Password changed for user {user.id}")

        update_data = {
            "lastPasswordChanged": user.lastPasswordChanged.isoformat(),
        }
        log_crud_action(
            action=ActionType.PASSWORD_CHANGE,
            user=current_user["userId"],
            user_full_name=current_user["fullName"],
            role=current_user["roleName"],
            entity_id=userId,
            table="user",
            message=f"{userName} changed their password",
            updated_data=update_data,
            log_type="auth",
            is_system_config=False,
        )
    except IntegrityError:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a wrong password format."
        )
    return {"Password Updated"}

#Reset password - identity proven via NRIC + DOB (no email step). Rate-limited
#because this is now the ONLY factor gating a reset, not a second factor
#alongside an emailed link like before.
@router.put("/user/request_reset_password/")
@rate_limit(global_bucket, tokens_required=1)
def request_reset_password(account: schemas_account.RequestResetPasswordBase, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_nric(db=db, nric=account.nric)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.nric_DateOfBirth != account.nric_DateOfBirth:
        raise HTTPException(status_code=404, detail="Invalid Details")

    if account.newPassword != account.confirmPassword:
        raise HTTPException(status_code=404, detail="Password do not match")

    try:
        #Check password format
        Validation_Service.validate_password_format(account.newPassword)
        #Hash password
        user.password = AuthService.get_password_hash(account.newPassword)
        #update modifiedById
        user.modifiedById=user.id
        #update last password changed time stamp
        user.lastPasswordChanged=datetime.now(sgt_tz)
        db.commit()

        # NRIC/DOB-resolved actor: the account resetting its own password via
        # identity verification is the actor. This flow is unauthenticated (no
        # JWT session), so "SYSTEM" must never be used here.
        log_crud_action(
            action=ActionType.PASSWORD_CHANGE,
            user=user.id,
            user_full_name=user.nric_FullName,
            role=user.roleName,
            entity_id=user.id,
            table="user",
            message=f"{user.nric_FullName} reset their password via NRIC/DOB verification",
            updated_data={"lastPasswordChanged": user.lastPasswordChanged.isoformat()},
            log_type="auth",
        )
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
    username = current_user["fullName"]
    db_user = await crud_user.update_user_User(db=db, userId=userId, user=user,modified_by=userId,username=username)
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

    original_picture_url = db_user.profilePicture

    try:
        # # Delete old profile picture from Cloudinary**
        if db_user.profilePicture:
            old_public_id = db_user.profilePicture.split("/")[-1].split(".")[0]  # Extract public ID
            cloudinary.uploader.destroy(f"profile_pictures/{old_public_id}")

        # Open the image
        image = Image.open(BytesIO(await file.read()))
        # Read and convert image
        if image.mode == "RGBA":
            image = image.convert("RGB")

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

        log_crud_action(
            action=ActionType.UPDATE,
            user=current_user["userId"],
            user_full_name=current_user["fullName"],
            role=current_user["roleName"],
            entity_id=user_id,
            table="user",
            message=f"{current_user['fullName']} updated their profile picture",
            original_data={"profilePicture": original_picture_url},
            updated_data={"profilePicture": db_user.profilePicture},
        )

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

    original_picture_url = db_user.profilePicture

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

        log_crud_action(
            action=ActionType.DELETE,
            user=current_user["userId"],
            user_full_name=current_user["fullName"],
            role=current_user["roleName"],
            entity_id=user_id,
            table="user",
            message=f"{current_user['fullName']} deleted their profile picture",
            original_data={"profilePicture": original_picture_url},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting profile picture: {str(e)}")

    return {"message": "Profile picture deleted successfully"}