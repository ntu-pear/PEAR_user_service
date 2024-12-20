from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
#from app.models.user_role_model import UserRole
from app.schemas.user_role import UserRoleRead, UserRoleCreate, UserRoleUpdate
from ..crud import user_role_crud as crud_role_user
from app.database import get_db

router = APIRouter()

@router.get("/user_roles/{user_role_id}", response_model=UserRoleRead)
def read_user_role(user_role_id: int, db: Session = Depends(get_db)):
    db_user_role = crud_role_user.get_user_role(db, user_role_id=user_role_id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role 
@router.get("/user_roles_id/{user_id}", response_model=list[UserRoleRead])
def read_user_role(user_Id: int, db: Session = Depends(get_db)):
    db_user_role = crud_role_user.get_user_role_userId(db, user_Id=user_Id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role 


@router.get("/user_roles", response_model=list[UserRoleRead])
def read_user_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = crud_role_user.get_all_user_roles(db,skip=skip, limit=limit)
    return roles

@router.get("/user_by_roles", response_model=list[UserRoleRead])
def read_user_by_roles(role: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = crud_role_user.get_user_by_roles(db=db, role=role, skip=skip, limit=limit)
    return roles

@router.post("/user_roles", response_model=UserRoleCreate)
def create_new_user_role(user_role: UserRoleCreate, db: Session = Depends(get_db)):
    return crud_role_user.create_user_role(db=db, user_role=user_role)

@router.put("/user_roles/{user_role_id}", response_model=UserRoleRead)
def update_existing_user_role(user_role_id: int, user_role: UserRoleUpdate, db: Session = Depends(get_db)):
    db_user_role =crud_role_user.update_user_role(db, user_role_id=user_role_id, user_role=user_role)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role

@router.delete("/user_roles/{user_role_id}", response_model=UserRoleRead)
def delete_user_role(user_role_id: int, db: Session = Depends(get_db)):
    db_user_role = crud_role_user.delete_user_role(db, user_role_id=user_role_id)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role

@router.delete("/user_roles_userID/{user_Id}", response_model=list[UserRoleRead])
def delete_user_role(userId: int, db: Session = Depends(get_db)):
    db_user_role = crud_role_user.delete_user_role_userId(db, userId=userId)
    if db_user_role is None:
        raise HTTPException(status_code=404, detail="User role not found")
    return db_user_role