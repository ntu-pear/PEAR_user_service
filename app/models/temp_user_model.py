from sqlalchemy import BigInteger, Column, Integer, String, Date,DateTime, ForeignKey
from app.database import Base



class Temp_User(Base):
    __tablename__ = 'TABLE_TEMP_USER'

    id = Column(Integer, primary_key=True)
    firstName = Column(String(255),nullable=False)
    lastName = Column(String(255),nullable=False)
    preferredName = Column(String(255))
    nric = Column(String(9), unique=True, nullable=False)
    address = Column(String(255),nullable=False)
    dateOfBirth = Column(Date,nullable=False)
    gender = Column(String(1),nullable=False)
    contactNo = Column(String(32),unique=True, nullable=False)
    email = Column(String(255), unique=True,nullable=False)
    role = Column(String(15), nullable=False)