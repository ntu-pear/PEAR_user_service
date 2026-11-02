from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mssql import JSON
from sqlalchemy.sql import func
from app.database import Base
import pytz

class AdminConfig(Base):
    __tablename__ = "TABLE_ADMIN_CONFIG"
    __table_args__ = (
        CheckConstraint("ISJSON(configBlob) = 1", name="CK_admin_config_json_valid"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    configBlob = Column(JSON, nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    modifiedById = Column(String(255), nullable=False)

    def get_modified_date_sgt(self):
        """Convert modifiedDate to Singapore Time (SGT)"""
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))
