from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Response, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user 
from ..crud import role_crud as crud_role
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..schemas import user_auth
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from app.service import validation_service as Validation_Service
from app.models.user_model import User
from typing import List
import cloudinary
import cloudinary.uploader
from PIL import Image
from io import BytesIO
from typing import Optional

# import rate limiter
from ..rate_limiter import TokenBucket, rate_limit

global_bucket = TokenBucket(rate=5, capacity=10)

router = APIRouter(
    tags=["admin"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

# Profile Picture Max Size
MAX_SIZE = (300, 300)  # Max image size (300x300)

# Function to assert if the user is an admin
def assert_admin(token_data: dict):
    if token_data.get("roleName") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User is not authorised")

# standardise successful responses
def create_success_response(data: dict):
    return {"status": "success", "data": data}

#Create Acc, unverified
@router.post("/admin/create_account/", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
async def create_user(user: schemas_user.TempUserCreate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user=crud_user.create_user(db=db, user=user, created_by=current_user["userId"])
    if db_user:
        #Send registration email
        token = EmailService.generate_email_token(db_user.id, db_user.email)
        await EmailService.send_registration_email(db_user.email, token)
   
    return schemas_user.AdminRead.from_orm(db_user)

@router.get("/admin/{userId}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
def get_user_by_id(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return schemas_user.AdminRead.from_orm(db_user)

@router.get("/admin/get_nric/{userId}")
@rate_limit(global_bucket, tokens_required=1)
def get_user_nric(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user.nric

@router.post("/admin/get_users_by_fields", response_model=schemas_user.UserPaginationResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_users_by_fields(*, fields: schemas_user.AdminSearch, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), 
page: int = 0, page_size: Optional[int] = 10, sort_by: Optional[str] = Query(None, description="Column to sort by (must match a User field)."),
sort_dir: str = Query("asc", description="'asc' or 'desc'"), db: Session = Depends(get_db),):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_users, total_count = crud_user.get_users_by_fields(
        db=db,
        page=page,
        page_size=page_size,
        fields=fields,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    if db_users is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Convert ORM objects to Pydantic models
    users_data = [schemas_user.AdminRead.from_orm(user) for user in db_users]

    return {
        "total": total_count,
        "page":page,
        "page_size": page_size,
        "users": users_data
    }



@router.get("/admin/get_guardian/{nric}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
def read_guadrian_nric(nric: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_guardian_nric(db=db, nric=nric)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return schemas_user.AdminRead.from_orm(db_user)

@router.get("/admin/", response_model=schemas_user.UserPaginationResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_all_users(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), page: Optional[int]= 0, page_size:Optional[int]=10, db: Session = Depends(get_db)):
    
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    #Only Admin can read all users
    db_users, total_count = crud_user.get_users(db=db, page=page,page_size=page_size)
    if db_users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    # Convert ORM objects to Pydantic models
    users_data = [schemas_user.AdminRead.from_orm(user) for user in db_users]

    return {
        "total": total_count,
        "page":page,
        "page_size": page_size,
        "users": users_data
    }

@router.get("/admin/get_email/{email}", response_model=schemas_user.AdminRead)
@rate_limit(global_bucket, tokens_required=1)
async def get_user_by_email(email: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas_user.AdminRead.from_orm(db_user)

@router.put("/admin/{userId}", response_model=schemas_user.AdminRead)
def update_user_by_admin(userId: str, user: schemas_user.UserUpdate_Admin,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.update_user_Admin(db=db, userId=userId, user=user,modified_by=current_user["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas_user.AdminRead.from_orm(db_user)

@router.put("/admin/reset_and_update_users_role/")
def reset_and_update_users_role(request: schemas_user.UpdateUsersRoleRequest,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    updated_users = []
    failed_updates=[]
    update_list = request.users_Id
    db_users = crud_role.get_users_by_role(role_name=request.role, page=1, page_size=10, db=db)
    #No updates for admin role
    if request.role != "ADMIN":
        for user in db_users["users"]:
            if user["id"] in update_list:
                #remove user from update list
                update_list.remove(user["id"])
            else:
                #cannot remove admin
                if request.role != "ADMIN":
                    #remove user's role
                    db_user=crud_user.update_users_role_admin(db=db, userId = user["id"], roleName= None,modified_by=current_user["userId"])
                    if db_user:
                        updated_users.append({"users_id": db_user.id, "FullName":db_user.nric_FullName, "role": db_user.roleName})

        for userId in update_list:
            db_user=crud_user.update_users_role_admin(db=db, userId=userId, roleName=request.role,modified_by=current_user["userId"])
            if db_user:
                updated_users.append({"users_id": db_user.id, "FullName":db_user.nric_FullName, "role": db_user.roleName})
            if db_user is None:
                failed_updates.append({"users_id": userId, "error": "User not found"})
    return {"Updated Users": updated_users, "Failed Updates":failed_updates}

@router.delete("/admin/{userId}", response_model=schemas_user.AdminRead)
def delete_user(userId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    if (current_user["userId"] == userId):
        raise HTTPException(status_code=404, detail="No self delete")

    #delete user from db
    db_user = crud_user.delete_user(db=db, userId=userId)
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas_user.AdminRead.from_orm(db_user)


@router.delete("/admin/soft_delete/{userId}", response_model=schemas_user.AdminRead)
def admin_soft_delete_user(userId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
                db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    if (current_user["userId"] == userId):
        raise HTTPException(status_code=404, detail="No self delete")

    # delete user from db
    db_user = crud_user.soft_delete_admin_user(db=db, userId=userId)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas_user.AdminRead.from_orm(db_user)

@router.post("/admin/user/{userId}/upload_profile_pic/", status_code=status.HTTP_200_OK)
async def upload_profile_picture(userId: str, file: UploadFile = File(...), current_user=Depends(AuthService.get_current_user), db: Session = Depends(get_db),):
    assert_admin(current_user)
    db_user = crud_user.get_user(db, userId)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Validate format
    Validation_Service.validate_profile_picture_format(file)

    try:
        # Remove old picture from Cloudinary
        if db_user.profilePicture:
            old_id = db_user.profilePicture.rsplit("/", 1)[-1].split(".")[0]
            cloudinary.uploader.destroy(f"profile_pictures/{old_id}")

        # Resize & convert
        img = Image.open(BytesIO(await file.read()))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail(MAX_SIZE)

        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        # Upload new picture to Cloudinary
        res = cloudinary.uploader.upload(
            buf,
            folder="profile_pictures",
            public_id=f"user_{userId}_profile_picture",
            overwrite=True
        )
        url = res.get("secure_url")

        # Persist in DB
        db_user.profilePicture = url
        db_user.modifiedById  = current_user["userId"]
        db.commit()
        db.refresh(db_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload profile picture: {e}"
        )

    return {"message": "Profile picture uploaded successfully", "file_url": url}


@router.get("/admin/user/{userId}/profile_pic/", status_code=status.HTTP_200_OK)
def get_profile_picture(userId: str, current_user=Depends(AuthService.get_current_user), db: Session = Depends(get_db),):
    assert_admin(current_user)
    user = crud_user.get_user(db, userId)
    if not user or not user.profilePicture:
        raise HTTPException(status_code=404, detail="No profile picture set")

    return {"image_url": user.profilePicture}


@router.delete("/admin/user/{userId}/delete_profile_pic/", status_code=status.HTTP_200_OK)
def delete_profile_picture(userId: str, current_user=Depends(AuthService.get_current_user), db: Session = Depends(get_db),):
    assert_admin(current_user)
    user = crud_user.get_user(db, userId)
    if not user or not user.profilePicture:
        raise HTTPException(status_code=404, detail="No profile picture found.")
    # Delete from Cloudinary
    public_id = user.profilePicture.rsplit("/", 1)[-1].split(".")[0]
    try:
        cloudinary.uploader.destroy(f"profile_pictures/{public_id}")
    except Exception:
        # log if desired, but continue
        pass

    # Clear DB field
    user.profilePicture = None
    user.modifiedById  = current_user["userId"]
    db.commit()
    db.refresh(user)

    return {"message": "Profile picture deleted successfully"}