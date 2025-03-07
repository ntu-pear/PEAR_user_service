from sqlalchemy.orm import Session
from ..models.patient_allocation_model import PatientAllocation
from ..schemas.patient_allocation import PatientAllocationCreate, PatientAllocationUpdate

def get_patient_allocation(db: Session, patient_id: str):
    return db.query(PatientAllocation).filter(PatientAllocation.patientId == patient_id).first()

def get_patient_allocations(db: Session, skip: int = 0, limit: int = 10):
    return db.query(PatientAllocation).order_by(PatientAllocation.patientId).offset(skip).limit(limit).all()

def create_patient_allocation(db: Session, patient_allocation: PatientAllocationCreate, created_by: int):
    db_patient_allocation = PatientAllocation(**patient_allocation.model_dump(),createdById=created_by,modifiedById=created_by)
    db.add(db_patient_allocation)
    db.commit()
    db.refresh(db_patient_allocation)
    return db_patient_allocation

def update_patient_allocation(db: Session, patient_id: str, patient_allocation: PatientAllocationUpdate, modified_by:str):
    db_patient_allocation = db.query(PatientAllocation).filter(PatientAllocation.patientId == patient_id).first()
    if db_patient_allocation:
        db_patient_allocation.modifiedById = modified_by
        # Update only provided fields
        for field, value in patient_allocation.model_dump(exclude_unset=True).items():
            setattr(db_patient_allocation, field, value)
        db.commit()
        db.refresh(db_patient_allocation)
    return db_patient_allocation

def delete_patient_allocation(db: Session, patient_id: str):
    db_patient_allocation = db.query(PatientAllocation).filter(PatientAllocation.patientId == patient_id).first()
    if db_patient_allocation:
        db.delete(db_patient_allocation)
        db.commit()
    return db_patient_allocation