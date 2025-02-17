from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import pytz
class User_Session(Base):
    __tablename__ = 'TABLE_SESSIONS'

    id = Column(String(20), primary_key=True, index=True)# Unique session identifier  
    user_id = Column(String(255), ForeignKey('TABLE_USER.id'),nullable=False)  # Link to the user table
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    expired_at = Column(DateTime, nullable=False)  # Time when session expires
    access_Token = Column(String, nullable=False)
    refresh_Token = Column(String, nullable=False)

    #Relationship to User table
    users = relationship('User', back_populates='user_session')

    def get_created_date_sgt(self):
        """Convert createdDate to Singapore Time (SGT)"""
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))
    def get_expired_at_sgt(self):
        """Convert expired_at to Singapore Time (SGT)"""
        if self.expired_at.tzinfo is None:
            return self.expired_at.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))
        return self.expired_at.astimezone(pytz.timezone("Asia/Singapore"))