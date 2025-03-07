from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PatientAllocationBase(BaseModel):
    patientId: str
    active: bool
    doctorId: str
    gameTherapistId: str
    supervisorId: str
    caregiverId: str
    guardianId: str
    tempDoctorId: Optional[str]=None
    tempCaregiverId: Optional[str]=None
    guardian2Id: Optional[str]=None

class PatientAllocationCreate(PatientAllocationBase):
    pass

class PatientAllocationUpdate(BaseModel):
    patientId: Optional[str]=None
    active: Optional[bool]=None
    doctorId: Optional[str]=None
    gameTherapistId: Optional[str]=None
    supervisorId: Optional[str]=None
    caregiverId: Optional[str]=None
    guardianId: Optional[str]=None
    tempDoctorId: Optional[str]=None
    tempCaregiverId: Optional[str]=None
    guardian2Id: Optional[str]=None

class PatientAllocationRead(PatientAllocationBase):
    pass

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }