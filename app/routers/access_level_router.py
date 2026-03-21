from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from ..database import get_db
from ..crud import access_level_crud
from ..schemas.access_level import AccessLevelCreate, AccessLevelUpdate, AccessLevelRead
from ..schemas import user_auth
from ..service import user_auth_service as AuthService

router = APIRouter(prefix="/access-levels", tags=["Access Levels"])

@router.get("/", response_model=list[AccessLevelRead])
def read_access_levels(
    db: Session = Depends(get_db),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user)
):
    return access_level_crud.get_all_access_levels(db)

@router.get("/{access_level_id}", response_model=AccessLevelRead)
def read_access_level(
    access_level_id: str,
    db: Session = Depends(get_db),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user)
):
    db_obj = access_level_crud.get_access_level_by_id(db, access_level_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Access level not found.")
    return db_obj

@router.post("/create", response_model=AccessLevelRead)
def create_new_access_level(
    data: AccessLevelCreate,
    db: Session = Depends(get_db),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user)
):
    if current_user["roleName"] != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not authorised")

    new_id = uuid.uuid4().hex[:8].upper()
    return access_level_crud.create_access_level(
        db=db,
        data=data,
        new_id=new_id,
        created_by=current_user["userId"]
    )

@router.put("/update/{access_level_id}", response_model=AccessLevelRead)
def update_existing_access_level(
    access_level_id: str,
    data: AccessLevelUpdate,
    db: Session = Depends(get_db),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user)
):
    if current_user["roleName"] != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not authorised")

    db_obj = access_level_crud.get_access_level_by_id(db, access_level_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Access level not found.")

    return access_level_crud.update_access_level(
        db=db,
        db_obj=db_obj,
        data=data,
        modified_by=current_user["userId"]
    )

@router.delete("/delete/{access_level_id}", response_model=AccessLevelRead)
def delete_existing_access_level(
    access_level_id: str,
    db: Session = Depends(get_db),
    current_user: user_auth.TokenData = Depends(AuthService.get_current_user)
):
    if current_user["roleName"] != "ADMIN":
        raise HTTPException(status_code=403, detail="User is not authorised")

    db_obj = access_level_crud.get_access_level_by_id(db, access_level_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Access level not found.")

    access_level_crud.delete_access_level(db, db_obj)
    return db_obj