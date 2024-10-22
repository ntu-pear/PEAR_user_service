from sqlalchemy import BigInteger, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from .user_role_model import UserRole
from .privacy_level_setting_model import PrivacyLevelSetting

class User(Base):
    __tablename__ = 'TABLE_USER'

    id = Column(Integer, primary_key=True)
    active = Column(String(1),default='Y',nullable=False)
    firstName = Column(String(255),nullable=False)
    lastName = Column(String(255),nullable=False)
    preferredName = Column(String(255))
    nric = Column(String(9), unique=True, nullable=False)
    address = Column(String(255),nullable=False)
    dateOfBirth = Column(DateTime,nullable=False)
    gender = Column(String(1),nullable=False)
    contactNo = Column(String(32),nullable=False)
    allowNotification = Column(String(1),default='Y',nullable=False)
    profilePicture = Column(String(32))
    lockoutReason = Column(String(255))
    loginTimeStamp = Column(DateTime,nullable=False)
    lastPasswordChanged = Column(DateTime,nullable=False)
    status = Column(String(50),nullable=False)
    userName = Column(String(255), unique=True,nullable=False)
    email = Column(String(255), unique=True,nullable=False)
    emailConfirmed = Column(String(1), default='N', nullable=False)
    passwordHash = Column(String(255),nullable=False)
    securityStamp = Column(String(255))
    concurrencyStamp = Column(String(255))
    phoneNumber = Column(String(32))
    phoneNumberConfirmed = Column(String(1), default='N', nullable=False)
    twoFactorEnabled = Column(String(1), default='N', nullable=False)
    lockOutEnd = Column(DateTime)
    lockOutEnabled = Column(String(1))
    accessFailedCount = Column(BigInteger)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)
    modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)


    # Explicitly define the relationship to created privacy settings
    # createdPrivacySettings = relationship('PrivacyLevelSetting', foreign_keys=[PrivacyLevelSetting.createdById])

    roles = relationship('UserRole', back_populates='user', foreign_keys=[UserRole.userId])
