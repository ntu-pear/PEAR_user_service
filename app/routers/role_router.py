from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.role import RoleCreate, RoleUpdate, Role
from ..crud.role_crud import get_role, get_roles, create_role, update_role, delete_role,get_users_by_role
from ..database import get_db

router = APIRouter()

@router.get("/roles/{roleId}", response_model=Role)
def read_role(token:str,roleId: int, db: Session = Depends(get_db)):
    db_role = get_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/", response_model=list[Role])
def read_roles(token:str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/roles/", response_model=RoleCreate )
def create_new_role(token:str, role: RoleCreate, db: Session = Depends(get_db)):
    return create_role(db=db, role=role)

@router.put("/roles/{roleId}", response_model=Role)
def update_existing_role(token:str, roleId: int, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = update_role(db, roleId=roleId, role=role)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{roleId}", response_model=Role)
def delete_exisiting_role(token:str, roleId: int, db: Session = Depends(get_db)):
    db_role = delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles/{role_name}/users")
def get_users_for_role(token:str, role_name: str, db: Session = Depends(get_db)):
    users = get_users_by_role(role_name, db)
    if "error" in users:
        raise HTTPException(status_code=404, detail=users["error"])
    return users