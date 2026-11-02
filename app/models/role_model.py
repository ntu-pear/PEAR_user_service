from sqlalchemy import Column, Boolean, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import pytz

class Role(Base):
    __tablename__ = "TABLE_ROLES"

    id = Column(String(8), primary_key=True)
    isDeleted = Column(Boolean, default=False, nullable=False)
    roleName = Column(String(255), unique=True, nullable=False)
    description = Column(String(1000), nullable=True)

    accessLevelId = Column(String(8), ForeignKey("TABLE_ACCESS_LEVELS.id"), nullable=False)

    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    createdById = Column(String(255), nullable=False)
    modifiedById = Column(String(255), nullable=False)

    accessLevel = relationship("AccessLevel", back_populates="roles", lazy="joined")
    users = relationship("User", back_populates="role")

    def get_created_date_sgt(self):
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))

    def get_modified_date_sgt(self):
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))