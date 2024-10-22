from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user_role_model import UserRole
from app.schemas.user_role import UserRoleRead, UserRoleCreate, UserRoleUpdate
from app.crud.user_role_crud import *
from app.database import get_db

router = APIRouter()

@router.get("/user_roles/{user_role_id}", response_model=UserRoleRead)
def read_user_role(user_role_id: int, db: Session = Depends(get_db)):
    db_user_role = get_user_role(db, user_role_id=user_role_id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role 

@router.get("/user_roles", response_model=list[UserRoleRead])
def read_user_roles(userId: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = get_user_roles(db, userId=userId, skip=skip, limit=limit)
    return roles

@router.get("/user_by_roles", response_model=list[UserRoleRead])
def read_user_by_roles(role: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = get_user_by_roles(db=db, role=role, skip=skip, limit=limit)
    return roles

@router.post("/user_roles", response_model=UserRoleRead)
def create_new_user_role(user_role: UserRoleCreate, db: Session = Depends(get_db)):
    return create_user_role(db=db, user_role=user_role)

@router.put("/user_roles/{user_role_id}", response_model=UserRoleRead)
def update_existing_user_role(user_role_id: int, user_role: UserRoleUpdate, db: Session = Depends(get_db)):
    db_user_role = update_user_role(db, user_role_id=user_role_id, user_role=user_role)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role

@router.delete("/user_roles/{user_role_id}", response_model=UserRoleRead)
def delete_user_role(user_role_id: int, db: Session = Depends(get_db)):
    db_user_role = delete_user_role(db, user_role_id=user_role_id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role
