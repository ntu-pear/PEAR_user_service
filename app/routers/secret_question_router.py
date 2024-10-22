from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.secret_question import SecretQuestionCreate, SecretQuestionUpdate, SecretQuestion
from ..crud.secret_question_crud import get_secret_question, get_secret_questions, create_secret_question, update_secret_question, delete_secret_question
from ..database import get_db

router = APIRouter()

@router.get("/secret_questions/{question_id}", response_model=SecretQuestion)
def read_secret_question(question_id: int, db: Session = Depends(get_db)):
    db_question = get_secret_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Secret question not found")
    return db_question

@router.get("/secret_questions", response_model=list[SecretQuestion])
def read_secret_questions(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    questions = get_secret_questions(db, skip=skip, limit=limit)
    return questions

@router.post("/secret_questions", response_model=SecretQuestion)
def create_new_secret_question(secret_question: SecretQuestionCreate, db: Session = Depends(get_db)):
    return create_secret_question(db=db, secret_question=secret_question)

@router.put("/secret_questions/{question_id}", response_model=SecretQuestion)
def update_existing_secret_question(question_id: int, secret_question: SecretQuestionUpdate, db: Session = Depends(get_db)):
    db_question = update_secret_question(db, question_id=question_id, secret_question=secret_question)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Secret question not found")
    return db_question

@router.delete("/secret_questions/{question_id}", response_model=SecretQuestion)
def delete_secret_question(question_id: int, db: Session = Depends(get_db)):
    db_question = delete_secret_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Secret question not found")
    return db_question
