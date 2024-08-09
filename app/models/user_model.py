from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "USER"

    id = Column(Integer, primary_key=True, index=True) 
    active = Column(String(1), default='Y', nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    preferredName = Column(String(255))
    nric = Column(String(9), unique=True, nullable=False)
    address = Column(String(255),nullable=False)
    dateOfBirth = Column(DateTime, nullable=False)
    gender = Column(String(1), nullable=False)
    contactNo = Column(String(32), nullable=False)
    allowNotifcation = Column(String(1), default='Y', nullable=False)
    profilePicture = Column(String(32))
    lockoutReason = Column(String(255))
    
    loginTimeStamp = Column(DateTime, nullable=False)
    lastPasswordChanged = Column(DateTime, nullable=False)
    status = Column(String(255), nullable=False)

    userName = Column(String(255),nullable=False)
    email = Column(String(255),nullable=False)
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

    createdDate = Column(DateTime,nullable=False)
    modifiedDate = Column(DateTime, default=datetime.now(), nullable=False)
    createdById = Column(ForeignKey("USER.id"), nullable=False)
    modifiedbyId = Column(ForeignKey("USER.id"), nullable=False)

# Ensure other models follow similar changes for consistency
