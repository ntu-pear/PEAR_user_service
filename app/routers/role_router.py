from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.role import RoleCreate, RoleUpdate, RoleRead
from ..schemas import user_auth
from ..crud.role_crud import get_role, get_roles, create_role, update_role, delete_role,get_users_by_role
from ..database import get_db
from ..service import user_auth_service as AuthService

router = APIRouter()

@router.get("/roles/{roleId}", response_model=RoleRead)
def read_role(roleId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = get_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/", response_model=list[RoleRead])
def read_roles(current_user: user_auth.TokenData = Depends(AuthService.get_current_user), skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    roles = get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/roles/", response_model=RoleRead )
def create_new_role(role: RoleCreate,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    return create_role(db=db, role=role, created_by=current_user["userId"])

@router.put("/roles/{roleId}", response_model=RoleRead)
def update_existing_role(roleId: str, role: RoleUpdate, current_user: user_auth.TokenData = Depends(AuthService.get_current_user),db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = update_role(db, roleId=roleId, role=role, modified_by=current_user["userId"])
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{roleId}", response_model=RoleRead)
def delete_exisiting_role(roleId: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/{role_name}/users")
def get_users_for_role(role_name: str,current_user: user_auth.TokenData = Depends(AuthService.get_current_user), db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    users = get_users_by_role(role_name, db)
    if "error" in users:
        raise HTTPException(status_code=404, detail=users["error"])
    return users