from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user_crud as crud_user
from ..schemas import user as schemas_user
from ..service.email_service import send_registration_email,generate_email_token, confirm_token,send_confirmation_email
from app.models.user_model import User

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)
#Create Acc, unverified
@router.post("/users/create_account/", response_model=schemas_user.TempUserCreate)
async def create_user(token: str, user: schemas_user.TempUserCreate, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    if not userDetails:
        raise HTTPException(status_code=404, detail="Invalid Token")
    if (userDetails.roleName != "Admin"):
         raise HTTPException(status_code=404, detail="User is not authorised")
    db_user=crud_user.create_user(db=db, user=user)
    if db_user:
        #Send registration email
        token = generate_email_token(user.email)
        await send_registration_email(user.email, token)
   
    return db_user
#Verify Acc, add password
@router.post("/users/verify_account/", response_model=schemas_user.UserBase)
async def verify_user(token: str, user: schemas_user.UserCreate, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    if not userDetails:
        raise HTTPException(status_code=404, detail="Invalid Token")
    db_user = crud_user.verify_user(db=db, user=user)
    if db_user:
        #Email Confirmation
        token = generate_email_token(user.email)
        await send_confirmation_email(user.email, token)

    return db_user

@router.get("/users/{userId}", response_model=schemas_user.UserRead)
def read_user(token: str, userId: int, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    db_user = crud_user.get_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/users/", response_model=list[schemas_user.UserRead])
def read_users(token:str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    users = crud_user.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/users/get_email/{email}", response_model=schemas_user.UserRead)
async def get_user_by_email(token:str, email: str, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    db_user = crud_user.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{userId}", response_model=schemas_user.UserUpdate)
def update_user(token:str, userId: int, user: schemas_user.UserUpdate, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    db_user = crud_user.update_user(db=db, userId=userId, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/users/{userId}", response_model=schemas_user.UserBase)
def delete_user(token: str, userId: int, db: Session = Depends(get_db)):
    userDetails= confirm_token(token)
    db_user = crud_user.delete_user(db=db, userId=userId)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/users/reset_password/{token}")
async def reset_user_password(token: str, newPassword: str, db: Session = Depends(get_db)):
    try:
        userDetails = confirm_token(token) 
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.email == userDetails.get("email")).first()
    #return user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = newPassword
    db.commit()
    
    return {"Successfully changed Password"}
