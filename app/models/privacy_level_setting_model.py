from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PrivacyLevelSetting(Base):
    __tablename__ = 'PRIVACY_LEVEL_SETTING'

    id = Column(Integer, primary_key=True)
    active = Column(String(1),default='Y', nullable=False)
    roleId = Column(Integer, ForeignKey('TABLE_ROLES.id'), nullable=False)  # FK to Role
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
