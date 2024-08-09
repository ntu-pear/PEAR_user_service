from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user

router = APIRouter()

@router.post("/users/", response_model=schemas_user.UserBase)
def create_user(user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    return crud_user.create_user(db=db, user=user)

@router.get("/users/{user_id}", response_model=schemas_user.UserBase)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user

@router.get("/users/", response_model=list[schemas_user.UserBase])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    return users

@router.put("/users/{user_id}", response_model=schemas_user.UserBase)
def update_user(user_id: int, user: schemas_user.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud_user.update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user

@router.delete("/users/{user_id}", response_model=schemas_user.UserBase)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud_user.delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return db_user
