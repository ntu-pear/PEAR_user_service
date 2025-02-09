from sqlalchemy import Column, Boolean, Integer, Enum as SqlEnum, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class Role_Names(enum.Enum):
    ADMIN= "ADMIN"
    DOCTOR= "DOCTOR"
    GAME_THERAPIST = "GAME THERAPIST"
    CAREGIVER = "CAREGIVER"
    SUPERVISOR = "SUPERVISOR"
    GUARDIAN = "GUARDIAN"

class Role(Base):
    __tablename__ = 'TABLE_ROLES'

    id = Column(String(255), primary_key=True)
    active = Column(Boolean, default=True, nullable=False)
    roleName = Column(SqlEnum(Role_Names), unique=True, nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)  # Ensure default value
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # Ensure it's updated
    
    #createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    #modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(String(255),nullable=False)
    modifiedById = Column(String(255),nullable=False) 

    # Use back_populates instead of backref for privacy settings
    privacyLevelSettings = relationship('PrivacyLevelSetting', back_populates='role')

    # Back-reference to users
    users = relationship('User', back_populates='role')  # One-to-Many relationship