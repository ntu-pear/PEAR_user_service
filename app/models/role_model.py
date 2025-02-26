from sqlalchemy import Column, Boolean, BigInteger, Integer, Enum as SqlEnum, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
import pytz

class RolePrivacyStatus(enum.Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Role(Base):
    __tablename__ = 'TABLE_ROLES'

    id = Column(String(8), primary_key=True)
    active = Column(Boolean, default=True, nullable=False)
    roleName = Column(String(255), unique=True, nullable=False)
    privacyLevelSensitive = Column(SqlEnum(RolePrivacyStatus), nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)  # Ensure default value
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # Ensure it's updated
    
    #createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    #modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(String(255),nullable=False)
    modifiedById = Column(String(255),nullable=False) 

    # Back-reference to users
    users = relationship('User', back_populates='role')  # One-to-Many relationship
    def get_created_date_sgt(self):
        """Convert createdDate to Singapore Time (SGT)"""
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))

    def get_modified_date_sgt(self):
        """Convert modifiedDate to Singapore Time (SGT)"""
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))