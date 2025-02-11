from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
class User_Session(Base):
    __tablename__ = 'TABLE_SESSIONS'

    id = Column(String(20), primary_key=True, index=True)# Unique session identifier  user_id = Column(Integer, ForeignKey('TABLE_USER.id'))  # Link to the user table
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    expired_at = Column(DateTime, nullable=False)  # Time when session expires
    access_Token = Column(String, nullable=False)
    refresh_Token = Column(String, nullable=False)
