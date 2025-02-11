from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..models.user_model import User
from ..schemas.role import RoleCreate, RoleUpdate
from fastapi import HTTPException, status
import uuid


def get_role(db: Session, roleId: str):
    return db.query(Role).filter(Role.id == roleId).first()

def get_roles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Role).order_by(Role.id).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate, created_by:str):
    # Generate a unique ID with a fixed length of 8
    while True:
        unique_id = role.roleName[0] + str(uuid.uuid4().hex[:7])
        # Ensure the total length is 8 characters
        roleId =unique_id[:8]  # Truncate to 8 if necessary
        existing_role_id = db.query(Role).filter(Role.id == roleId).first()
        if not existing_role_id:
            break

    # Check if the role already exists
    existing_role = db.query(Role).filter(Role.roleName == role.roleName).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A role with this name already exists."
        )
    
    db_role = Role(**role.model_dump(),createdById=created_by,modifiedById=created_by,id=roleId)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
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
    db.delete(db_role)
    db.commit()
    return db_role

def get_users_by_role(role_name: str, db: Session):
    # Fetch the role by name
    role = db.query(Role).filter(Role.roleName == role_name).first()
    if not role:
        return {"error": "Role not found"}
    
    # Get all users associated with this role
    users = db.query(User).filter(User.roleName == role.roleName).all()
    return [{"id": user.id, "FullName": user.nric_FullName, "Role": user.roleName} for user in users]