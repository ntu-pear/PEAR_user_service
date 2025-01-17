from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.user_secret_question import UserSecretQuestionCreate, UserSecretQuestionUpdate, UserSecretQuestion
from ..crud.user_secret_question_crud import get_user_secret_question, get_user_secret_questions, create_user_secret_question, update_user_secret_question, delete_user_secret_question
from ..database import get_db

router = APIRouter()

@router.get("/user_secret_questions/{question_id}", response_model=UserSecretQuestion)
def read_user_secret_question(question_id: int, db: Session = Depends(get_db)):
    db_question = get_user_secret_question(db, user_secret_question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="User secret question not found")
    return db_question

@router.get("/user_secret_questions", response_model=list[UserSecretQuestion])
def read_user_secret_questions(userId: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    questions = get_user_secret_questions(db, userId=userId, skip=skip, limit=limit)
    return questions

@router.post("/user_secret_questions", response_model=UserSecretQuestion)
def create_new_user_secret_question(user_secret_question: UserSecretQuestionCreate, db: Session = Depends(get_db)):
    return create_user_secret_question(db=db, user_secret_question=user_secret_question)

@router.put("/user_secret_questions/{question_id}", response_model=UserSecretQuestion)
def update_existing_user_secret_question(question_id: int, user_secret_question: UserSecretQuestionUpdate, db: Session = Depends(get_db)):
    db_question = update_user_secret_question(db, user_secret_question_id=question_id, user_secret_question=user_secret_question)
    if db_question is None:
        raise HTTPException(status_code=404, detail="User secret question not found")
    return db_question

@router.delete("/user_secret_questions/{question_id}", response_model=UserSecretQuestion)
def delete_user_secret_question(question_id: int, db: Session = Depends(get_db)):
    db_question = delete_user_secret_question(db, user_secret_question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="User secret question not found")
    return db_question
