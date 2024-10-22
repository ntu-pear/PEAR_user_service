from sqlalchemy.orm import Session
from app.models.user_role_model import UserRole
from app.schemas.user_role import UserRoleCreate, UserRoleUpdate
from app.models.role_model import Role

# Get a single user role by user role ID
def get_user_role(db: Session, user_role_id: int):
    return db.query(UserRole).filter(UserRole.id == user_role_id).first()

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
