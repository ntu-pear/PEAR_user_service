from datetime import datetime, date
from enum import Enum

from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..models.user_model import User
from ..schemas.role import RoleBase, RoleUpdate
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import uuid
from ..logger.logger_utils import log_crud_action, ActionType, serialize_data
from ..models.access_level_model import AccessLevel
#Currently the role sensitivity is causing issue, so need to use sqlachemy to dict conversion.
def sqlalchemy_to_dict(obj):
    """Convert SQLAlchemy model to dict, handling enums and datetimes"""
    result = {}
    for c in obj.__table__.columns:
        val = getattr(obj, c.name)
        if isinstance(val, Enum):
            val = val.value  # convert Enum to primitive
        elif isinstance(val, (datetime, date)):
            val = val.isoformat()
        result[c.name] = val
    return result

def enrich_access_level(access_level):
    access_level.isEditable = not access_level.isSystem
    access_level.isDeletable = not access_level.isSystem
    return access_level


def get_role_by_id(db: Session, roleId: str):
    return db.query(Role).filter(Role.id == roleId).first()

def get_role_by_name(db: Session, roleName: str):
    return db.query(Role).filter(Role.roleName == roleName).first()


from sqlalchemy.orm import joinedload

def get_roles(db: Session, page:int, page_size:int): 
    max_page_size = 100
    page_size = min(page_size, max_page_size)
    page = max(page, 0)
    offset = page * page_size

    query = db.query(Role)\
        .options(joinedload(Role.accessLevel))\
        .filter(Role.isDeleted == False)

    total_count = query.count()

    roles = query.order_by(Role.roleName)\
        .offset(offset)\
        .limit(page_size)\
        .all()
    for role in roles:
        if role.accessLevel:
            role.accessLevel = enrich_access_level(role.accessLevel)

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "roles": roles
    }

def create_role(db: Session, role: RoleBase, current_user: dict):

    # Check if the role already exists
    existing_role = db.query(Role).filter(Role.roleName == role.roleName).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A role with this name already exists."
        )
    db_access_level = db.query(AccessLevel).filter(AccessLevel.id == role.accessLevelId).first()
    if not db_access_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected access level does not exist."
        )

    # Generate a unique ID with a fixed length of 8
    while True:
        unique_id = role.roleName[0].upper() + str(uuid.uuid4().hex[:7])  # Ensure first char is uppercase
        roleId = unique_id[:8]  # Ensure exactly 8 characters
        existing_role_id = db.query(Role).filter(Role.id == roleId).first()
        if not existing_role_id:
            break

    # Use a transaction to ensure rollback on error
    try:
        db_role = Role(**role.model_dump(),createdById=current_user["userId"],modifiedById=current_user["userId"],id=roleId)
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
    except IntegrityError as e:
        # Rollback transaction if any IntegrityError occurs
        db.rollback()
        print(e.orig)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred: possibly a duplicate unique field."
        )
    # Serialize the data properly (handles datetime and other types)
    updated_data = sqlalchemy_to_dict(db_role)

    log_crud_action(
        action=ActionType.CREATE,
        user=current_user["userId"],
        user_full_name=current_user["fullName"],
        role=current_user["roleName"],
        entity_id=roleId,
        table='role',
        message=f"Created role: {role.roleName}",
        updated_data=updated_data,
    )
    return db_role

def update_role(db: Session, roleId: str, role: RoleUpdate, modified_by:str):
    db_role = db.query(Role).filter(Role.id == roleId).first()
    if role.roleName is not None:
        existing_role = db.query(Role).filter(
            Role.roleName == role.roleName,
            Role.id != roleId
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A role with this name already exists."
            )
    if role.accessLevelId is not None:
        db_access_level = db.query(AccessLevel).filter(AccessLevel.id == role.accessLevelId).first()
        if not db_access_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected access level does not exist."
            )
    if db_role:
        #update modified by Who
        db_role.modifiedById = modified_by
        #update role fields
            # Update only provided fields
        for field, value in role.model_dump(exclude_unset=True).items():
            setattr(db_role, field, value)
        db.commit()
        db.refresh(db_role)
    return db_role

def delete_role(db: Session, roleId: str):
    db_role = db.query(Role).filter(Role.id == roleId).first()

    if not db_role:
        raise HTTPException(
            status_code=400,
            detail="Role not found."
        )

    db_users = db.query(User).filter(User.roleName == db_role.roleName).first()
    if db_users:
        raise HTTPException(
            status_code=400,
            detail="There are users with the role"
        )

    db_role.isDeleted = True
    db.commit()
    db.refresh(db_role)

    return db_role

def get_users_by_role(role_name: str, page: int, page_size: int, db: Session):
    # Fetch the role by name
    role = db.query(Role).filter(Role.roleName == role_name).first()
    if not role:
        return {"error": "Role not found"}

    # Pagination logic
    offset = page * page_size
    # Get total number of users with the given role
    total_count = db.query(User).filter(User.roleName == role.roleName).count()

    # Get users associated with this role, applying pagination
    users = db.query(User).filter(User.roleName == role.roleName).order_by(User.id).offset(offset).limit(page_size).all()

    # Return paginated result
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "users": [{"id": user.id, "FullName": user.nric_FullName, "Role": user.roleName} for user in users]
    }