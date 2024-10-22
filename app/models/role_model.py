from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = 'ROLES'

    id = Column(Integer, primary_key=True)
    active = Column(String(1),default='Y', nullable=False)
    role = Column(String(255), unique=True, nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)  # Ensure default value
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # Ensure it's updated
    
    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)
    modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)

    # Relationships
    # createdBy = relationship('User', foreign_keys=[createdById])
    # modifiedBy = relationship('User', foreign_keys=[modifiedById])

    # Use back_populates instead of backref for privacy settings
    privacyLevelSettings = relationship('PrivacyLevelSetting', back_populates='role')
