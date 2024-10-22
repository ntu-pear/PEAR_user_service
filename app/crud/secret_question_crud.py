from sqlalchemy.orm import Session
from ..models.secret_question_model import SecretQuestion
from ..schemas.secret_question import SecretQuestionCreate, SecretQuestionUpdate

def get_secret_question(db: Session, question_id: int):
    return db.query(SecretQuestion).filter(SecretQuestion.id == question_id).first()

def get_secret_questions(db: Session, skip: int = 0, limit: int = 10):
    return db.query(SecretQuestion).order_by(SecretQuestion.id).offset(skip).limit(limit).all()

def create_secret_question(db: Session, secret_question: SecretQuestionCreate):
    db_question = SecretQuestion(**secret_question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def update_secret_question(db: Session, question_id: int, secret_question: SecretQuestionUpdate):
    db_question = db.query(SecretQuestion).filter(SecretQuestion.id == question_id).first()
    if db_question:
        for key, value in secret_question.dict().items():
            setattr(db_question, key, value)
        db.commit()
        db.refresh(db_question)
    return db_question

def delete_secret_question(db: Session, question_id: int):
    db_question = db.query(SecretQuestion).filter(SecretQuestion.id == question_id).first()
    if db_question:
        db.delete(db_question)
        db.commit()
    return db_question
