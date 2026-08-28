from argparse import Action
from venv import logger
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy import func
from ..models.user_model import User
from ..schemas import user as schemas_User
from ..schemas import user as UserUpdate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.service import validation_service as Validation_Service
from app.service import email_service as EmailService
from sqlalchemy import and_
import uuid
import cloudinary
import cloudinary.uploader
from typing import Optional
from app.logger.logger_utils import log_crud_action, ActionType
from app.utils.error_utils import add_error, raise_if_errors


# whitelist of sortable columns for get_users_by_fields
ALLOWED_SORT_COLUMNS = {
    "id":                User.id,
    "preferredName":     User.preferredName,
    "nric_FullName":     User.nric_FullName,
    "email":             User.email,
    "loginTimeStamp":    User.loginTimeStamp,
    "roleName":          User.roleName,
    "createdDate":       User.createdDate,
}

def get_user(db: Session, userId: str):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, page: int, page_size:int ):
    # Maximum page size limit to prevent excessively large queries
    max_page_size = 100
    page_size = min(page_size, max_page_size)  # Enforce max page size
    page = max(page, 0)  # Default to page 0 if the page number is less than 0
    offset = page  * page_size  # Calculate the offset

    # Query to get all users
    query = db.query(User)

    # Total count of users (without pagination)
    total_count = query.count()

    # Get the users with pagination
    users = query.order_by(User.id).offset(offset).limit(page_size).all()

    return users, total_count

def get_guardian_nric(db: Session, nric= str):
    return db.query(User).filter((User.nric==nric) &(User.roleName=="GUARDIAN")).first()

def get_users_by_fields(db: Session, page: int, page_size: int, fields: schemas_User.AdminSearch,
sort_by: Optional[str] = None, sort_dir: str = "asc",) -> tuple[list[User], int]:
    filters = []

    if fields.id:
        filters.append(User.id == fields.id)
    if fields.preferredName:
       filters.append(User.preferredName.ilike(f"%{fields.preferredName}%")) #partial matching
    if fields.nric_FullName:
        filters.append(User.nric_FullName.ilike(f"%{fields.nric_FullName}%")) #partial matching
    if fields.nric:
        filters.append(User.nric == fields.nric)
    if fields.email:
        filters.append(User.email.ilike(f"%{fields.email}%"))
    if fields.verified is not None:
        filters.append(User.verified == fields.verified)
    if fields.isDeleted is not None:
        filters.append(User.isDeleted == fields.isDeleted)
    if fields.twoFactorEnabled is not None:
        filters.append(User.twoFactorEnabled == fields.twoFactorEnabled)
    if fields.roleName:
        filters.append(User.roleName == fields.roleName)
    if fields.lockOutEnabled is not None:
        filters.append(User.lockOutEnabled == fields.lockOutEnabled)

    # Pagination Logic
    # Maximum page size limit to prevent excessively large queries
    max_page_size = 100
    page_size = min(page_size, max_page_size)  # Enforce max page size
    page = max(page, 0)  # Default to page 0 if the page number is less than 0
    offset = page * page_size  # Calculate the offset


    query=db.query(User).filter(and_(*filters))

    total_count = query.count()  # Get total number of records

    # apply dynamic ordering
    if sort_by in ALLOWED_SORT_COLUMNS:
        col = ALLOWED_SORT_COLUMNS[sort_by]
        if sort_dir.lower() == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())
    else:
        # default sort
        query = query.order_by(User.nric_FullName.asc())

    users = query.offset(offset).limit(page_size).all()  # Apply pagination

    return users, total_count

#Update User
async def update_user_User(db: Session, userId: str, user: schemas_User.UserUpdate_User, modified_by,username):
    stmt = update(User).where(User.id == userId)

    original_user = db.query(User).filter(User.id == userId).first()
    original_data = {
        "email": original_user.email,
        "contactNo": original_user.contactNo,
        "fullName": original_user.nric_FullName,
        "profilePicture": original_user.profilePicture,
    }
    message = f"Updated user: {original_user.nric_FullName}"
    if not original_user:
        raise ValueError(f"User {userId} not found")

    updated_fields = {}
    # update modified by who
    stmt = stmt.values(modifiedById=modified_by)
    for field, value in user.model_dump(exclude_unset=True).items():
        if field =="contactNo":
            Validation_Service.validate_contactNo(value)
        if field != "email":
            stmt = stmt.values({field: value})
        if field == "email":
            #Send confirmation email if email is changed
            email_Token = EmailService.generate_email_token(userId, value)
            await EmailService.send_confirmation_email(value, email_Token)
        else:
            updated_fields[field] = value
    updated_fields['modifiedById'] = modified_by


    db.execute(stmt)
    db.commit()
    updated_user = db.query(User).filter(User.id == userId).first()
    updated_data = {
        "email": updated_user.email,
        "contactNo": updated_user.contactNo,
        "fullName": updated_user.nric_FullName,
        "profilePicture": original_user.profilePicture,
        "modified_by" : updated_user.modifiedDate
    }

    message = f"Updated user: {original_user.nric_FullName} ({userId})"
    log_crud_action(
            action=ActionType.UPDATE,
            user=modified_by,
            role=updated_user.roleName,
            message=message,
            user_full_name=original_user.nric_FullName,
            entity_id=userId,
            original_data=original_data,
            updated_data=updated_data,
            table='USER'
    )

    # Fetch the updated user to return it
    db_user = db.query(User).filter(User.id == userId).first()
    return updated_user

#Admin update other user's account
def update_user_Admin(
    db: Session,
    userId: str,
    user: schemas_User.UserUpdate_Admin,
    modified_by
):
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        return None

    update_data = user.model_dump(exclude_unset=True)
    errors = []

    # email
    if "email" in update_data and update_data["email"]:
        try:
            update_data["email"] = Validation_Service.validate_email(update_data["email"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "email", str(e.detail))

        if "email" in update_data and not any(err["loc"][-1] == "email" for err in errors):
            existing_user_email = (
                db.query(User)
                .filter(
                    func.lower(User.email) == update_data["email"],
                    User.id != userId
                )
                .first()
            )
            if existing_user_email:
                add_error(errors, "email", "A user with this email already exists.")

    # nric
    if "nric" in update_data and update_data["nric"]:
        try:
            update_data["nric"] = Validation_Service.validate_nric(update_data["nric"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric", str(e.detail))

        if "nric" in update_data and not any(err["loc"][-1] == "nric" for err in errors):
            existing_user_nric = (
                db.query(User)
                .filter(
                    func.upper(User.nric) == update_data["nric"],
                    User.id != userId
                )
                .first()
            )
            if existing_user_nric:
                add_error(errors, "nric", "A user with this NRIC already exists.")

    # contact number
    if "contactNo" in update_data:
        try:
            update_data["contactNo"] = Validation_Service.validate_contactNo(update_data["contactNo"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "contactNo", str(e.detail))

        if (
            "contactNo" in update_data
            and update_data["contactNo"]
            and not any(err["loc"][-1] == "contactNo" for err in errors)
        ):
            existing_user_contact = (
                db.query(User)
                .filter(
                    User.contactNo == update_data["contactNo"],
                    User.id != userId
                )
                .first()
            )
            if existing_user_contact:
                add_error(errors, "contactNo", "A user with this contact number already exists.")

    # date of birth
    if "nric_DateOfBirth" in update_data and update_data["nric_DateOfBirth"]:
        try:
            update_data["nric_DateOfBirth"] = Validation_Service.validate_dob(
                update_data["nric_DateOfBirth"]
            )
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric_DateOfBirth", str(e.detail))

    # preferred name
    if "preferredName" in update_data and update_data["preferredName"]:
        try:
            update_data["preferredName"] = Validation_Service.validate_uppercase_name(
                update_data["preferredName"],
                "preferredName"
            )
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "preferredName", str(e.detail))

    # full name
    if "nric_FullName" in update_data and update_data["nric_FullName"]:
        try:
            update_data["nric_FullName"] = Validation_Service.validate_uppercase_name(
                update_data["nric_FullName"],
                "nric_FullName"
            )
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric_FullName", str(e.detail))

    # optional extra check for required lockout reason when enabled
    if update_data.get("lockOutEnabled") is True:
        lockout_reason = update_data.get("lockOutReason", db_user.lockOutReason)
        if not lockout_reason or not str(lockout_reason).strip():
            add_error(errors, "lockOutReason", "Lockout Reason is required when Lockout Enabled is Yes.")

    raise_if_errors(errors)

    stmt = (
        update(User)
        .where(User.id == userId)
        .values(modifiedById=modified_by, **update_data)
    )

    db.execute(stmt)
    db.commit()

    updated_user = db.query(User).filter(User.id == userId).first()
    return updated_user

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

    # If the user does not exist, raise a 404 error
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    #delete user pic id from cloudinary
    if db_user.profilePicture:
        public_id = db_user.profilePicture.split("/")[-1].split(".")[0]  # Extracts `user_Ufa53ec48e2f_profile_picture`
        cloudinary.uploader.destroy(f"profile_pictures/{public_id}")

    ## Delete the user from the database
    db.delete(db_user)
    db.commit()
    return db_user

def soft_delete_admin_user(db: Session, userId: str):
    db_user = db.query(User).filter(User.id == userId).first()
    # If the user does not exist, raise a 404 error
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Ensure user is not an admin
    if db_user.roleName == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another admin"
        )
    # If already soft deleted, optionally raise or skip
    if db_user.isDeleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="User is already deleted"
        )
    #soft delete, hence it only sets the isDeleted flag to True.
    db_user.isDeleted = True
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
        if not Validation_Service.verify_userDetails(db_user, user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Details do not match with pre-registered details"
    )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has already been verified"
        )
    if (user.password != user.confirm_Password):
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password does not match"
        )

    # Use a transaction to ensure rollback on error
    try:
        #Check password format
        Validation_Service.validate_password_format(user.password)
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
    create_data = user.model_dump()
    errors = []

    # Validate + normalize NRIC
    if create_data.get("nric"):
        try:
            create_data["nric"] = Validation_Service.validate_nric(create_data["nric"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric", str(e.detail))

    # Validate + normalize email
    if create_data.get("email"):
        try:
            create_data["email"] = Validation_Service.validate_email(create_data["email"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "email", str(e.detail))

    # Validate + normalize contact number
    if "contactNo" in create_data:
        try:
            create_data["contactNo"] = Validation_Service.validate_contactNo(create_data["contactNo"])
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "contactNo", str(e.detail))

    # Validate DOB
    if create_data.get("nric_DateOfBirth"):
        try:
            create_data["nric_DateOfBirth"] = Validation_Service.validate_dob(
                create_data["nric_DateOfBirth"]
            )
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric_DateOfBirth", str(e.detail))

    # Validate uppercase full name
    if create_data.get("nric_FullName"):
        try:
            create_data["nric_FullName"] = Validation_Service.validate_uppercase_name(
                create_data["nric_FullName"],
                "nric_FullName"
            )
        except HTTPException as e:
            if isinstance(e.detail, list):
                errors.extend(e.detail)
            else:
                add_error(errors, "nric_FullName", str(e.detail))

    # Duplicate checks only if field passed validation
    if create_data.get("email") and not any(err["loc"][-1] == "email" for err in errors):
        existing_email = (
            db.query(User)
            .filter(func.lower(User.email) == create_data["email"])
            .first()
        )
        if existing_email:
            add_error(errors, "email", "A user with this email already exists.")

    if create_data.get("nric") and not any(err["loc"][-1] == "nric" for err in errors):
        existing_nric = (
            db.query(User)
            .filter(func.upper(User.nric) == create_data["nric"])
            .first()
        )
        if existing_nric:
            add_error(errors, "nric", "A user with this NRIC already exists.")

    if (
        create_data.get("contactNo")
        and not any(err["loc"][-1] == "contactNo" for err in errors)
    ):
        existing_contact = (
            db.query(User)
            .filter(User.contactNo == create_data["contactNo"])
            .first()
        )
        if existing_contact:
            add_error(errors, "contactNo", "A user with this contact number already exists.")

    # Stop here if any validation errors collected
    raise_if_errors(errors)

    # Generate unique user id
    while True:
        unique_id = "U" + str(uuid.uuid4().hex[:11])
        userId = unique_id[:11]
        existing_user_id = db.query(User).filter(User.id == userId).first()
        if not existing_user_id:
            break

    try:
        db_user = User(
            **create_data,
            createdById=created_by,
            modifiedById=created_by,
            id=userId
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    except IntegrityError:
        db.rollback()
        # fallback for DB-level uniqueness/race conditions
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[
                {
                    "loc": ["body", "non_field"],
                    "msg": "An error occurred: possibly a duplicate unique field."
                }
            ]
        )

    return db_user

def update_user(db: Session, user_id: str, user_update: UserUpdate, modified_by: int):
    """Function to update an existing user"""

    # Retrieve the user from the database
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    original_data = db_user.__dict__.copy()
    # Update fields if provided
    update_data = user_update.model_dump(exclude_unset=True)  # Exclude unset fields
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db_user.modifiedById = modified_by  # Track who modified the user

    db.commit()
    db.refresh(db_user)


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

    db_user.isDeleted = False
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
        isDeleted = True,
        lockoutReason=lockout_reason,
        modifiedById=modified_by
    )

    db.execute(stmt)
    db.commit()

    # Fetch and return the updated user
    db_user = db.query(User).filter(User.id == userId).first()
    return db_user

def update_user_profile_picture(db: Session, user_id: str, profile_url: Optional[str], modified_by: str) -> Optional[User]:
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(
            profilePicture=profile_url,
            modifiedById=modified_by
        )
        .execution_options(synchronize_session="fetch")
    )
    db.execute(stmt)
    db.commit()
    return db.query(User).filter(User.id == user_id).first()

def get_changed_fields(original_data, updated_data):
    changed = {}
    for key, new_value in updated_data.items():
        old_value = original_data.get(key)
        if old_value != new_value:
            changed[key] = {"old": old_value, "new": new_value}
    return changed