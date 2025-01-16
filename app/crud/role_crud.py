from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..models.user_model import User
from ..schemas.role import RoleCreate, RoleUpdate
from fastapi import HTTPException, status

def get_role(db: Session, roleId: int):
    return db.query(Role).filter(Role.id == roleId).first()

def get_roles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Role).order_by(Role.id).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate, created_by:int):
    
    # Check if the role already exists
    existing_role = db.query(Role).filter(Role.roleName == role.roleName).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A role with this name already exists."
        )
    
    db_role = Role(**role.dict(),createdById=created_by,modifiedById=created_by)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, roleId: int, role: RoleUpdate, modified_by:int):
    db_role = db.query(Role).filter(Role.id == roleId).first()
    if db_role:
        #update modified by Who
        db_role.modifiedById = modified_by
        #update role fields
        for key, value in role.dict().items():
            #check if value is not empty
            if value != "":
                setattr(db_role, key, value)
        db.commit()
        db.refresh(db_role)
    return db_role

def delete_role(db: Session, roleId: int):
    db_role = db.query(Role).filter(Role.id == roleId).first()
    if db_role:
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
    return [{"id": user.id, "FullName": user.nric_FullName} for user in users]