from app.utils.utils import mask_nric
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user 
from ..crud import role_crud as crud_role
from ..schemas import user as schemas_user
from ..schemas import account as schemas_account
from ..schemas import user_auth
from ..schemas import admin_config as schemas_admin_config
from ..service import email_service as EmailService
from ..service import user_auth_service as AuthService 
from ..service import admin_config_service as AdminConfigService
from app.service import validation_service as Validation_Service
from app.models.user_model import User
from typing import List, Optional, Dict
import cloudinary
import cloudinary.uploader
from PIL import Image
from io import BytesIO
from typing import Optional
import csv, io, datetime    
import pytz

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

@router.get("/admin/user/{userId}", response_model=schemas_user.AdminRead)
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

@router.put("/admin/user/{userId}", response_model=schemas_user.AdminRead)
def update_user_by_admin(userId: str, user: schemas_user.UserUpdate_Admin,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_user = crud_user.update_user_Admin(db=db, userId=userId, user=user,modified_by=current_user["userId"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas_user.AdminRead.from_orm(db_user)

@router.put("/admin/reset_and_update_users_role/")
def reset_and_update_users_role(
    request: schemas_user.UpdateUsersRoleRequest,
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["roleName"] != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not authorised")

    updated_users = []
    failed_updates = []

    # Always copy
    update_list = list(request.users_Id)

    # Block updates for ADMIN role
    if request.role == "ADMIN":
        raise HTTPException(status_code=400, detail="ADMIN role cannot be updated")

    if update_list:
        selected_users = db.query(User).filter(User.id.in_(update_list)).all()
        selected_by_id = {u.id: u for u in selected_users}

        missing_ids = [uid for uid in update_list if uid not in selected_by_id]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "USER_NOT_FOUND",
                    "message": "One or more users were not found.",
                    "missing_users": missing_ids,
                },
            )

        conflicts = []
        for uid in update_list:
            u = selected_by_id[uid]
            if u.roleName is not None and u.roleName != request.role:
                conflicts.append(
                    {
                        "users_id": u.id,
                        "FullName": u.nric_FullName,
                        "current_role": u.roleName,
                        "requested_role": request.role,
                        "error": f"{u.nric_FullName} already has role {u.roleName}.",
                    }
                )

        if conflicts:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "USER_ALREADY_HAS_ROLE",
                    "message": "One or more selected users are already assigned a role.",
                    "conflicts": conflicts,  # list of {FullName, current_role, error, ...}
                },
            )

    db_users = crud_role.get_users_by_role(
        role_name=request.role,
        page=0,
        page_size=100000,
        db=db,
    )

    update_set = set(update_list)

    # Remove role from users who currently have it but are NOT selected
    for user in db_users.get("users", []):
        if user["id"] not in update_set:
            db_user = crud_user.update_users_role_admin(
                db=db,
                userId=user["id"],
                roleName=None,
                modified_by=current_user["userId"],
            )
            if db_user:
                updated_users.append(
                    {"users_id": db_user.id, "FullName": db_user.nric_FullName, "role": db_user.roleName}
                )

    # Assign role to selected users
    for userId in update_list:
        db_user = crud_user.update_users_role_admin(
            db=db,
            userId=userId,
            roleName=request.role,
            modified_by=current_user["userId"],
        )
        if db_user:
            updated_users.append(
                {"users_id": db_user.id, "FullName": db_user.nric_FullName, "role": db_user.roleName}
            )
        else:
            failed_updates.append({"users_id": userId, "error": "User not found"})

    return {"Updated Users": updated_users, "Failed Updates": failed_updates}


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

@router.get("/admin/users/export", response_class=StreamingResponse)
def export_users_csv(
    nric_fullname: Optional[str] = Query(None, alias="nric_FullName"),
    is_deleted: Optional[bool] = Query(None, alias="isDeleted"),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.get("roleName") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorised")

    filters = []
    if nric_fullname:
        filters.append(User.nric_FullName.ilike(f"%{nric_fullname}%"))
    if is_deleted is not None:
        filters.append(User.isDeleted == is_deleted)

    query = db.query(User)
    if filters:
        query = query.filter(and_(*filters))

    users = query.order_by(User.id).all()

    # Dynamically include ALL columns from the SQLAlchemy model
    column_names = [c.name for c in User.__table__.columns]

    EXCLUDE_COLS = {
        "password",
        "otp",
        "securityStamp",
        "concurrencyStamp",
        "captchaKey",
        "captchaFailedCount",
        "lastPasswordChanged",
    }
    exclude_lower = {c.lower() for c in EXCLUDE_COLS}
    column_names = [c for c in column_names if c.lower() not in exclude_lower]

    # Write CSV to memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(column_names)
    for u in users:
        row = [getattr(u, col) for col in column_names]
        writer.writerow(row)

    sgt = pytz.timezone("Asia/Singapore")
    ts = datetime.datetime.now(tz=sgt).strftime("%Y%m%d_%H%M%S")
    filename = f"users_export_{ts}.csv"

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/admin/config", response_model=schemas_admin_config.AdminConfigMapResponse)
@rate_limit(global_bucket, tokens_required=1)
def get_all_configs(
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.get("roleName") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorised")
    
    configs = AdminConfigService.get_all_configs(db)

    return configs


@router.put("/admin/config", response_model=schemas_admin_config.AdminConfigMapResponse)
@rate_limit(global_bucket, tokens_required=1)
def update_configs(
    configs: Dict[str, schemas_admin_config.ConfigValue],
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.get("roleName") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorised")
    
    existing_configs = AdminConfigService.get_all_configs(db)
    incoming_configs = configs

    if existing_configs:
        missing_keys = set(existing_configs.keys()) - set(incoming_configs.keys())
        extra_keys = set(incoming_configs.keys()) - set(existing_configs.keys())
        if missing_keys or extra_keys:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Configuration keys must match the existing set.",
                    "missing": missing_keys,
                    "extra": extra_keys,
                },
            )

    updated_configs = AdminConfigService.update_all_configs(
        db,
        incoming_configs,
        current_user["userId"],
    )

    return updated_configs
