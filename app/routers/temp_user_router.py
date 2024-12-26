from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import temp_user_crud as crud_user
from ..schemas import temp_user as schemas_user
from ..service.email_service import  send_registration_email,generate_email_token, confirm_token,send_confirmation_email
from app.models.temp_user_model import Temp_User

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/temp_users/", response_model=schemas_user.CreateTempUser)
async def create_user(user: schemas_user.CreateTempUser, db: Session = Depends(get_db)):
    
    db_user=crud_user.create_temp_user(db=db, user=user)
    if db_user:
        #Send registration email
        token = generate_email_token(user.email)#, user.userName)
        await send_registration_email(user.email, token)
   
    return db_user

@router.get("/temp_users/{userId}", response_model=schemas_user.ReadTempUser)
def read_user(userId: int, db: Session = Depends(get_db)):
    db_user = crud_user.get_temp_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/temp_users/", response_model=list[schemas_user.ReadTempUser])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud_user.get_temp_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/temp_users/get_email/{email}", response_model=schemas_user.ReadTempUser)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    db_user = crud_user.get_temp_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/temp_users/{userId}", response_model=schemas_user.UpdateTempUser)
def update_user(userId: int, user: schemas_user.UpdateTempUser, db: Session = Depends(get_db)):
    db_user = crud_user.update_temp_user(db=db, userId=userId, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/temp_users/{userId}", response_model=schemas_user.TempUserBase)
def delete_user(userId: int, db: Session = Depends(get_db)):
    db_user = crud_user.delete_temp_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

