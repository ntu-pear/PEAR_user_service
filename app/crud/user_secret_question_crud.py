from sqlalchemy.orm import Session
from ..models.user_secret_question_model import UserSecretQuestion
from ..schemas.user_secret_question import UserSecretQuestionCreate, UserSecretQuestionUpdate

def get_user_secret_question(db: Session, user_secret_question_id: int):
    return db.query(UserSecretQuestion).filter(UserSecretQuestion.id == user_secret_question_id).first()

def get_user_secret_questions(db: Session, userId: str, skip: int = 0, limit: int = 10):
    return db.query(UserSecretQuestion).filter(UserSecretQuestion.userId == userId).order_by(UserSecretQuestion.id).offset(skip).limit(limit).all()

def create_user_secret_question(db: Session, user_secret_question: UserSecretQuestionCreate):
    db_user_secret_question = UserSecretQuestion(**user_secret_question.dict())
    db.add(db_user_secret_question)
    db.commit()
    db.refresh(db_user_secret_question)
    return db_user_secret_question

def update_user_secret_question(db: Session, user_secret_question_id: int, user_secret_question: UserSecretQuestionUpdate):
    db_user_secret_question = db.query(UserSecretQuestion).filter(UserSecretQuestion.id == user_secret_question_id).first()
    if db_user_secret_question:
        for key, value in user_secret_question.dict().items():
            setattr(db_user_secret_question, key, value)
        db.commit()
        db.refresh(db_user_secret_question)
    return db_user_secret_question

def delete_user_secret_question(db: Session, user_secret_question_id: int):
    db_user_secret_question = db.query(UserSecretQuestion).filter(UserSecretQuestion.id == user_secret_question_id).first()
    if db_user_secret_question:
        db.delete(db_user_secret_question)
        db.commit()
    return db_user_secret_question
