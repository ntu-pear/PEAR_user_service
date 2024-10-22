from sqlalchemy.orm import Session
from ..models.user_model import User
from ..schemas.user import UserCreate, UserUpdate
from ..service import user_auth_service

def get_user(db: Session, userId: int):
    return db.query(User).filter(User.id == userId).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    # Hashes the password
    user.passwordHash=user_auth_service.get_password_hash(user.passwordHash)
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, userId: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        for key, value in user.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, userId: int):
    db_user = db.query(User).filter(User.id == userId).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
