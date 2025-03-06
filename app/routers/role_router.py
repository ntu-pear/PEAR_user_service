from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.role import RoleCreate, RoleUpdate, RoleRead, RolePaginationResponse
from ..schemas import user_auth
from ..crud import role_crud
from ..database import get_db
from ..service import user_auth_service as AuthService
from typing import Optional

router = APIRouter()

@router.get("/roles/{roleId}", response_model=RoleRead)
def read_role(roleId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.get_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/", response_model=RolePaginationResponse)
def read_roles(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), page: Optional[int] = 1, page_size: Optional[int]=10, db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    roles = role_crud.get_roles(db, page=page, page_size=page_size)
    return roles

@router.post("/roles/", response_model=RoleRead )
def create_new_role(role: RoleCreate,  current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    
    return role_crud.create_role(db=db, role=role, created_by=1)

@router.put("/roles/{roleId}", response_model=RoleRead)
def update_existing_role(roleId: str, role: RoleUpdate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.update_role(db, roleId=roleId, role=role, modified_by=current_user["userId"])
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{roleId}", response_model=RoleRead)
def delete_existing_role(roleId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/users/{role_name}")
def get_users_by_role(role_name: str,page:Optional[int]=1, page_size:Optional[int]=10,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    users = role_crud.get_users_by_role(role_name=role_name,page=page,page_size=page_size, db=db)
    if "error" in users:
        raise HTTPException(status_code=404, detail=users["error"])
    return users