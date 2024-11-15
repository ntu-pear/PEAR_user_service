from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..service.email_service import generate_confirmation_token, confirm_token,send_confirmation_email

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/users/", response_model=schemas_user.UserBase)
async def create_user(user: schemas_user.UserBase, db: Session = Depends(get_db)):
    #Email Confirmation
    token = generate_confirmation_token(user.email)
    await send_confirmation_email(user.email, token)
    #Send Phone
    return crud_user.create_user(db=db, user=user)

@router.get("/users/{userId}", response_model=schemas_user.UserBase)
def read_user(userId: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/users/", response_model=list[schemas_user.UserBase])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/users/get_email/{email}", response_model=schemas_user.UserBase)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{userId}", response_model=schemas_user.UserUpdate)
def update_user(userId: int, user: schemas_user.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud_user.update_user(db=db, userId=userId, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/users/{userId}", response_model=schemas_user.UserBase)
def delete_user(userId: int, db: Session = Depends(get_db)):
    db_user = crud_user.delete_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

