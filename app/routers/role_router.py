from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.role_model import Role
from ..schemas.role import RoleBase, RoleUpdate, RoleRead, AdminRolePaginationResponse,RoleNamePaginationResponse
from ..schemas import user_auth
from ..crud import role_crud
from ..database import get_db
from ..service import user_auth_service as AuthService
from typing import Optional

router = APIRouter()

@router.get("/roles_name/", response_model=RoleNamePaginationResponse)
def get_roles_name(page: Optional[int] = 0, page_size: Optional[int]=10, db: Session = Depends(get_db)):
    roles = role_crud.get_roles(db, page=page, page_size=page_size)
    return roles

@router.get("/roles/name/{name}", response_model=RoleBase)
def get_role_by_name(roleName: str , db: Session = Depends(get_db)):
    role= role_crud.get_role_by_name(db, roleName)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role
    
@router.get("/roles/{roleId}", response_model=RoleRead)
def read_role(roleId: str, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.get_role_by_id(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/", response_model=AdminRolePaginationResponse)
def read_roles(page: Optional[int] = 0, page_size: Optional[int]=10, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    
    roles = role_crud.get_roles(db, page=page, page_size=page_size)
    return roles

@router.post("/roles/create/", response_model=RoleRead )
def create_new_role(role: RoleBase,  current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    
    return role_crud.create_role(db=db, role=role, created_by=1)

@router.put("/roles/update/{roleId}", response_model=RoleRead)
def update_existing_role(roleId: str, role: RoleUpdate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.update_role(db, roleId=roleId, role=role, modified_by=current_user["userId"])
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/delete/{roleId}", response_model=RoleRead)
def delete_existing_role(roleId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = role_crud.delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/users/{role_name}")
def get_users_by_role(role_name: str,page:Optional[int]=0, page_size:Optional[int]=10,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    users = role_crud.get_users_by_role(role_name=role_name,page=page,page_size=page_size, db=db)
    if "error" in users:
        raise HTTPException(status_code=404, detail=users["error"])
    return users