from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from app.models.user_role_model import UserRole
from app.schemas.user_role import UserRoleCreate, UserRoleUpdate
from app.models.role_model import Role

# Get all users roles
def get_all_user_roles(db: Session, skip: int = 0, limit: int = 10):
    #sort according to UserID
    return db.query(UserRole).order_by(UserRole.userId).offset(skip).limit(limit).all()

# Get a single user role by user role ID
def get_user_role(db: Session, user_role_id: int):
    return db.query(UserRole).filter(UserRole.id == user_role_id).first()
# Get a single user role by userID
def get_user_role_userId(db: Session, user_Id: int):
    return db.query(UserRole).filter(UserRole.userId == user_Id).all()

def get_user_role_by_user(db: Session, user_id: int):
    return db.query(UserRole).filter(UserRole.userId == user_id).first()

# Get all user roles for a specific user, with optional pagination
def get_user_roles(db: Session, userId: int, skip: int = 0, limit: int = 10):
    return db.query(UserRole).filter(UserRole.userId == userId).order_by(UserRole.id).offset(skip).limit(limit).all()

# Get a list of users based on their role, with optional pagination
def get_user_by_roles(db: Session, role: str, skip: int = 0, limit: int = 10):
    role_id = db.query(Role).filter(Role.role == role).first()
    if role_id is None:
        return []
    user_roles = db.query(UserRole).filter(UserRole.roleId == role_id.id).order_by(UserRole.id).offset(skip).limit(limit).all()
    return user_roles

# Create a new user role
def create_user_role(db: Session, user_role: UserRoleCreate):

    db_user_role = UserRole(**user_role.dict())
    # Check if the combination already exists
    existing_role = db.query(UserRole).filter(and_(UserRole.userId == db_user_role.userId, UserRole.roleId == db_user_role.roleId)).first()
    if existing_role:
        raise HTTPException(status_code=404, detail="This user-role combination already exists.")
       
    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role

# Update an existing user role by user role ID
def update_user_role(db: Session, user_role_id: int, user_role: UserRoleUpdate):
    db_user_role = db.query(UserRole).filter(UserRole.id == user_role_id).first()
    if db_user_role is None:
        return None
    
    # Update the fields based on the provided user role update data
    db_user_role.userId = user_role.userId
    db_user_role.roleId = user_role.roleId
    
    db.commit()
    db.refresh(db_user_role)
    return db_user_role

# Delete an existing user role by user role ID
def delete_user_role(db: Session, user_role_id: int):
    db_user_role = db.query(UserRole).filter(UserRole.id == user_role_id).first()
    if db_user_role is None:
        return None
    
    db.delete(db_user_role)
    db.commit()
    return db_user_role

# Delete all existing user role by user ID
def delete_user_role_userId(db: Session, userId: int):
    db_user_role = db.query(UserRole).filter(UserRole.userId == userId).order_by(UserRole.id).all()
    
    if db_user_role is None:
        return None
    for role in db_user_role:
        db.delete(role)
    db.commit()
    return db_user_role

