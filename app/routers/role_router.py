from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.role import RoleCreate, RoleUpdate, Role
from ..crud.role_crud import get_role, get_roles, create_role, update_role, delete_role
from ..database import get_db

router = APIRouter()

@router.get("/roles/{roleId}", response_model=Role)
def read_role(roleId: int, db: Session = Depends(get_db)):
    db_role = get_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/roles", response_model=list[Role])
def read_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = get_roles(db, skip=skip, limit=limit)
    return roles

@router.post("/roles", response_model=Role)
def create_new_role(role: RoleCreate, db: Session = Depends(get_db)):
    return create_role(db=db, role=role)

@router.put("/roles/{roleId}", response_model=Role)
def update_existing_role(roleId: int, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = update_role(db, roleId=roleId, role=role)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{roleId}", response_model=Role)
def delete_exisiting_role(roleId: int, db: Session = Depends(get_db)):
    db_role = delete_role(db, roleId=roleId)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role
