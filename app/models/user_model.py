from sqlalchemy import BigInteger,Boolean, Column,Enum as SqlEnum, Integer, String, Date,DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
# Define an Enum for status
class UserStatus(enum.Enum):
    ANNUAL_LEAVE = "AL"
    MEDICAL_LEAVE= "MC"
    ACTIVE="ACTIVE"


class GenderStatus(enum.Enum):
    MALE = "M"
    FEMALE = "F"

class User(Base):
    __tablename__ = 'TABLE_USER'

    id = Column(String(255), primary_key=True)
    active = Column(Boolean,default=True,nullable=False)
    nric_FullName = Column(String(255), nullable=False)
    nric = Column(String(9), unique=True, nullable=False)
    nric_Address = Column(String(255),nullable=False)
    nric_DateOfBirth = Column(Date,nullable=False)
    nric_Gender = Column(SqlEnum(GenderStatus, values_callable=lambda x: [e.value for e in x]), nullable=False)
    preferredName= Column(String(255), nullable=True)
    contactNo = Column(String(32),nullable=False)
    contactNoConfirmed = Column(Boolean, default=False, nullable=False)
    allowNotification = Column(Boolean, default=False, nullable=False)
    profilePicture = Column(String(255))
    lockoutReason = Column(String(255))
    loginTimeStamp = Column(DateTime)#,nullable=False)
    lastPasswordChanged = Column(DateTime)#,nullable=False)
    status = Column(SqlEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)  # Enum for status
 
    email = Column(String(255), unique=True,nullable=False)
    emailConfirmed = Column(Boolean, default=False, nullable=False)
    password = Column(String(255))
    verified = Column(Boolean, default=False, nullable=False)

    securityStamp = Column(String(255))
    concurrencyStamp = Column(String(255))
    #phoneNumber = Column(String(32))
    #phoneNumberConfirmed = Column(String(1), default='N', nullable=False)
    twoFactorEnabled = Column(Boolean, default=False, nullable=False)
    lockOutEnd = Column(DateTime)
    lockOutEnabled = Column(Boolean, default=False, nullable=False)
    accessFailedCount = Column(BigInteger)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    secretKey = Column(String(6),nullable=True)
    otpFailedCount = Column(BigInteger, default="0")
    captchaKey = Column(String(6),nullable=True)
    captchaFailedCount = Column(BigInteger, default="0")


    createdById = Column(String(255), nullable=True)
    modifiedById = Column(String(255), nullable=True)
    #createdById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)
    #modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=True)

    # Explicitly define the relationship to created privacy settings
    # createdPrivacySettings = relationship('PrivacyLevelSetting', foreign_keys=[PrivacyLevelSetting.createdById])

    # Foreign key to Role table
    roleName = Column(String(255), ForeignKey('TABLE_ROLES.roleName'), nullable=False)
    # Relationship to Role table
    role = relationship('Role', back_populates='users')  # Many-to-One relationship
