from sqlalchemy import Column, Boolean, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import pytz
class PrivacyLevelSetting(Base):
    __tablename__ = 'PRIVACY_LEVEL_SETTING'

    id = Column(String(255), primary_key=True)
    active = Column(Boolean, default=True, nullable=False)
    roleId = Column(String(255), ForeignKey('TABLE_ROLES.id'), nullable=False)  # FK to Role
    privacyLevelSensitive = Column(BigInteger, nullable=False )
    privacyLevelNonSensitive = Column(BigInteger, nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)
    modifiedById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)

    # Relationship with Role
    role = relationship('Role', foreign_keys=[roleId], back_populates='privacyLevelSettings')

    def get_created_date_sgt(self):
        """Convert createdDate to Singapore Time (SGT)"""
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))

    def get_modified_date_sgt(self):
        """Convert modifiedDate to Singapore Time (SGT)"""
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))
