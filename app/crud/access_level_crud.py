from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.access_level_model import AccessLevel
from ..schemas.access_level import AccessLevelCreate, AccessLevelUpdate

RESERVED_SYSTEM_CODES = {"NONE", "LOW", "MEDIUM", "HIGH"}

def get_all_access_levels(db: Session):
    return db.query(AccessLevel).order_by(AccessLevel.levelRank.asc()).all()

def get_access_level_by_id(db: Session, access_level_id: str):
    return db.query(AccessLevel).filter(AccessLevel.id == access_level_id).first()

def get_access_level_by_code(db: Session, code: str):
    return db.query(AccessLevel).filter(AccessLevel.code == code).first()
def get_access_level_by_rank(db: Session, level_rank: int):
    return db.query(AccessLevel).filter(AccessLevel.levelRank == level_rank).first()

def create_access_level(db: Session, data: AccessLevelCreate, new_id: str, created_by: str):
    normalized_code = data.code.strip().upper()

    if normalized_code in RESERVED_SYSTEM_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This code is reserved for system access levels."
        )
    if data.levelRank in {0, 1, 2, 3}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ranks 0, 1, 2, and 3 are reserved for system access levels."
        )

    existing_code = get_access_level_by_code(db, normalized_code)
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access level code already exists."
        )

    existing_rank = get_access_level_by_rank(db, data.levelRank)
    if existing_rank:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access level rank already exists."
        )

    db_obj = AccessLevel(
        id=new_id,
        code=normalized_code,
        levelRank=data.levelRank,
        levelName=data.levelName.strip(),
        description=data.description.strip(),
        isSystem=False,
        createdById=created_by,
        modifiedById=created_by,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_access_level(db: Session, db_obj: AccessLevel, data: AccessLevelUpdate, modified_by: str):
    update_data = data.model_dump(exclude_unset=True)

    if db_obj.isSystem:
        disallowed = {"code", "levelRank", "levelName"} & set(update_data.keys())
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access levels only allow description updates."
            )
    else:
        if "code" in update_data and update_data["code"] is not None:
            normalized_code = update_data["code"].strip().upper()

            if normalized_code in RESERVED_SYSTEM_CODES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This code is reserved for system access levels."
                )

            existing_code = db.query(AccessLevel).filter(
                AccessLevel.code == normalized_code,
                AccessLevel.id != db_obj.id
            ).first()
            if existing_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access level code already exists."
                )

            update_data["code"] = normalized_code

        if "levelRank" in update_data and update_data["levelRank"] is not None:
            existing_rank = db.query(AccessLevel).filter(
                AccessLevel.levelRank == update_data["levelRank"],
                AccessLevel.id != db_obj.id
            ).first()
            if existing_rank:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access level rank already exists."
                )

    if "levelName" in update_data and update_data["levelName"] is not None:
        update_data["levelName"] = update_data["levelName"].strip()

    if "description" in update_data and update_data["description"] is not None:
        update_data["description"] = update_data["description"].strip()

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db_obj.modifiedById = modified_by
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_access_level(db: Session, db_obj: AccessLevel):
    if db_obj.isSystem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System access levels cannot be deleted."
        )

    if db_obj.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an access level that is assigned to roles."
        )

    db.delete(db_obj)
    db.commit()