from sqlalchemy import BigInteger, Column, Integer, String, Date,DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

from .role_model import Role
from .privacy_level_setting_model import PrivacyLevelSetting
 

class User(Base):
    __tablename__ = 'TABLE_USER'

    id = Column(Integer, primary_key=True)
    active = Column(String(1),default='Y',nullable=False)
    nric_FullName = Column(String(255), nullable=False)
    nric = Column(String(9), unique=True, nullable=False)
    nric_Address = Column(String(255),nullable=False)
    nric_DateOfBirth = Column(Date,nullable=False)
    nric_Gender = Column(String(1), nullable=False)
    preferredName= Column(String(255), nullable=True)
    contactNo = Column(String(32),nullable=False)
    contactNoConfirmed = Column(String(1), default='N', nullable=False)
    allowNotification = Column(String(1),default='Y',nullable=False)
    profilePicture = Column(String(32))
    lockoutReason = Column(String(255))
    loginTimeStamp = Column(DateTime)#,nullable=False)
    lastPasswordChanged = Column(DateTime)#,nullable=False)
    status = Column(String(50),default="ACTIVE",nullable=False)
 
    email = Column(String(255), unique=True,nullable=False)
    emailConfirmed = Column(String(1), default='F', nullable=False)
    password = Column(String(255))
    verified = Column(String(1), default="F", nullable=False)

    securityStamp = Column(String(255))
    concurrencyStamp = Column(String(255))
    #phoneNumber = Column(String(32))
    #phoneNumberConfirmed = Column(String(1), default='N', nullable=False)
    twoFactorEnabled = Column(String(1), default='N', nullable=False)
    lockOutEnd = Column(DateTime)
    lockOutEnabled = Column(String(1))
    accessFailedCount = Column(BigInteger)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    secretKey = Column(String(6),nullable=True)
    otpFailedCount = Column(BigInteger, default="0")
    captchaKey = Column(String(6),nullable=True)
    captchaFailedCount = Column(BigInteger, default="0")


    createdById = Column(Integer, nullable=False)
    modifiedById = Column(Integer, nullable=False)
    #createdById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)
    #modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)

    # Explicitly define the relationship to created privacy settings
    # createdPrivacySettings = relationship('PrivacyLevelSetting', foreign_keys=[PrivacyLevelSetting.createdById])

    # Foreign key to Role table
    roleName = Column(String(255), ForeignKey('TABLE_ROLES.roleName'), nullable=False)
    # Relationship to Role table
    role = relationship('Role', back_populates='users')  # Many-to-One relationship
