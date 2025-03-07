from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.patient_allocation import PatientAllocationCreate, PatientAllocationUpdate, PatientAllocationRead
from ..crud.patient_allocation_crud import get_patient_allocation, get_patient_allocations, create_patient_allocation, update_patient_allocation, delete_patient_allocation 
from ..database import get_db
from ..service import user_auth_service as AuthService
from ..schemas import user_auth

router = APIRouter()

@router.get("/patient_allocation/{patient_id}", response_model=PatientAllocationRead)
def read_patient_allocation(patient_id: str, db: Session = Depends(get_db)):
    db_patient_allocation = get_patient_allocation(db, patient_id=patient_id)
    if db_patient_allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return db_patient_allocation

@router.get("/patient_allocation", response_model=list[PatientAllocationRead])
def read_patient_allocations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    patient_allocations = get_patient_allocations(db, skip=skip, limit=limit)
    return patient_allocations

@router.post("/patient_allocation", response_model=PatientAllocationRead)
def create_new_patient_allocation(patient_allocation: PatientAllocationCreate, db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    
    return create_patient_allocation(db=db, patient_allocation=patient_allocation, created_by=1)

@router.put("/patient_allocation/{user_id}", response_model=PatientAllocationRead)
def update_existing_patient_allocation(patient_id: str, patient_allocation: PatientAllocationUpdate, db: Session = Depends(get_db)):
    #1) retrieve current user role name. must be guardian
    #2) retrieve current user role ID and search patient guardian table. must be valid
    #3) done
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_patient_allocation = update_patient_allocation(db=db, patient_id=patient_id, patient_allocation=patient_allocation, modified_by=1)
    if db_patient_allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return db_patient_allocation

@router.delete("/patient_allocation/{user_id}", response_model=PatientAllocationRead)
def delete_existing_patient_allocataion(patient_id: str, db: Session = Depends(get_db)):
    is_admin = current_user["roleName"] == "ADMIN"
    if not is_admin:
        raise HTTPException(status_code=404, detail="User is not authorised")
    db_patient_allocation = delete_patient_allocation(db=db, patient_id=patient_id)
    if db_patient_allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return db_patient_allocation
