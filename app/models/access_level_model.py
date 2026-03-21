from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import pytz

class AccessLevel(Base):
    __tablename__ = "TABLE_ACCESS_LEVELS"

    id = Column(String(8), primary_key=True)
    code = Column(String(50), unique=True, nullable=False)       # NONE, LOW, MEDIUM, HIGH, CUSTOM_X
    levelRank = Column(Integer, unique=True, nullable=False)                  # 0,1,2,3,4...
    levelName = Column(String(100), nullable=False)             # display label
    description = Column(String(500), nullable=False)

    isSystem = Column(Boolean, default=False, nullable=False)

    createdById = Column(String(255), nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedById = Column(String(255), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    roles = relationship("Role", back_populates="accessLevel")

    def get_created_date_sgt(self):
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))

    def get_modified_date_sgt(self):
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))