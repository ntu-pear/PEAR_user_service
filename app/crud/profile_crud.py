from venv import logger
from sqlalchemy.orm import Session
from sqlalchemy import update

from ..models.user_model import User

from ..schemas.user import UserCreate, UserUpdate, UserUpdate_Admin, TempUserCreate
from ..service import user_auth_service
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.service import user_service as UserService