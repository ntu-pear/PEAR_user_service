# from .utils import generate_passwd_hash
# from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Session
from ..models.user_model import User
from ..schemas.user import UserCreate, UserUpdate
from fastapi import Depends
from ..database import get_db

class UserService:
    async def get_user_by_email(email: str, db: Session = Depends(get_db)):
        return db.query(User).filter(User.email == email).first()
    
    async def get_user_by_name(name: str, db: Session = Depends(get_db)):
        return db.query(User).filter(User.name == name).first()
    