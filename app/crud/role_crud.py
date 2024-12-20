from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..schemas.role import RoleCreate, RoleUpdate
from fastapi import HTTPException, status

def get_role(db: Session, roleId: int):
    return db.query(Role).filter(Role.id == roleId).first()

def get_roles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Role).order_by(Role.id).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate):
    # Check if the role already exists
    existing_role = db.query(Role).filter(Role.id == role.id).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            #detail="A role with this name already exists."
            detail="User already has a role."
        )
    
    db_role = Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, roleId: int, role: RoleUpdate):
    db_role = db.query(Role).filter(Role.id == roleId).first()
    if db_role:
        for key, value in role.dict().items():
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
