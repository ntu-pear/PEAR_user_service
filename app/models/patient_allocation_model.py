from sqlalchemy import Column, Boolean, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

class PatientAllocation(Base):
    __tablename__ = "PATIENT_ALLOCATION"

    patientId = Column(String(12), primary_key=True)
    active = Column(Boolean, default=True, nullable=False)
    doctorId = Column(String(12), nullable=False)
    gameTherapistId = Column(String(12), nullable=False)
    supervisorId = Column(String(12), nullable=False)
    caregiverId = Column(String(12), nullable=False)
    guardianId = Column(String(12), nullable=False)
    tempDoctorId = Column(String(12))
    tempCaregiverId = Column(String(12))
    guardian2Id = Column(String(12))

    createdDate = Column(DateTime, server_default=func.now(), nullable=False)  # Ensure default value
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # Ensure it's updated
    createdById = Column(String(255), nullable=False)  # Changed to String
    modifiedById = Column(String(255), nullable=False)  # Changed to String
    

    privacy_level = relationship("PrivacyLevelSetting", back_populates="patients")