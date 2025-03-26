from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..models.user_model import User
from ..schemas.role import RoleCreate, RoleUpdate
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import uuid


def get_role(db: Session, roleId: str):
    return db.query(Role).filter(Role.roleName == roleId).first()

def get_roles(db: Session, page:int, page_size:int): 
    # Maximum page size limit to prevent excessively large queries
    max_page_size = 100
    page_size = min(page_size, max_page_size)  # Enforce max page size
    page = max(page, 0)  # Default to page 0 if the page number is less than 0
    offset = page* page_size  # Calculate the offset

    # Query to get all roles (no filters applied)
    query = db.query(Role)

    # Total count of roles (without pagination)
    total_count = query.count()

    # Get the roles with pagination
    roles= query.order_by(Role.id).offset(offset).limit(page_size).all()

    # Return the paginated response
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "roles": roles
    }

def create_role(db: Session, role: RoleCreate, created_by:str):

    # Check if the role already exists
    existing_role = db.query(Role).filter(Role.roleName == role.roleName).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A role with this name already exists."
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
        db_role = Role(**role.model_dump(),createdById=created_by,modifiedById=created_by,id=roleId)
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
    return db_role

def update_role(db: Session, roleId: str, role: RoleUpdate, modified_by:str):
    db_role = db.query(Role).filter(Role.id == roleId).first()
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role not found."
        )
    if db_role.roleName == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete Admin."
        )
    db.delete(db_role)
    db.commit()
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