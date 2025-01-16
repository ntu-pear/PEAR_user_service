from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.role import RoleCreate, RoleUpdate, RoleRead
from ..crud.role_crud import get_role, get_roles, create_role, update_role, delete_role,get_users_by_role
from ..database import get_db
from ..service.user_auth_service import decode_access_token

router = APIRouter()

@router.get("/roles/{roleId}", response_model=RoleRead)
def read_role(token:str,roleId: int, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    db_role = get_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/", response_model=list[RoleRead])
def read_roles(token:str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    roles = get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/roles/", response_model=RoleRead )
def create_new_role(token:str, role: RoleCreate, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    return create_role(db=db, role=role, created_by=userDetails["userId"])

@router.put("/roles/{roleId}", response_model=RoleRead)
def update_existing_role(token:str, roleId: int, role: RoleUpdate, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    db_role = update_role(db, roleId=roleId, role=role, modified_by=userDetails["userId"])
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{roleId}", response_model=RoleRead)
def delete_exisiting_role(token:str, roleId: int, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    if (userDetails["roleName"] != "ADMIN"):
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_role = delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/{role_name}/users",response_model=RoleRead)
def get_users_for_role(token:str, role_name: str, db: Session = Depends(get_db)):
    userDetails= decode_access_token(token)
    users = get_users_by_role(role_name, db)
    if "error" in users:
        raise HTTPException(status_code=404, detail=users["error"])
    return users