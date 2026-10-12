from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.access_level_model import AccessLevel
from ..schemas.access_level import AccessLevelCreate, AccessLevelUpdate
from ..logger.logger_utils import log_crud_action, ActionType

RESERVED_SYSTEM_CODES = {"NONE", "LOW", "MEDIUM", "HIGH"}

def enrich_access_level(access_level):
    access_level.isEditable = not access_level.isSystem
    access_level.isDeletable = not access_level.isSystem
    return access_level

def get_all_access_levels(db: Session):
    levels = db.query(AccessLevel).order_by(AccessLevel.levelRank.asc()).all()
    return [enrich_access_level(lvl) for lvl in levels]

def get_access_level_by_id(db: Session, access_level_id: str):
    return db.query(AccessLevel).filter(AccessLevel.id == access_level_id).first()

def get_access_level_by_code(db: Session, code: str):
    return db.query(AccessLevel).filter(AccessLevel.code == code).first()
def get_access_level_by_rank(db: Session, level_rank: int):
    return db.query(AccessLevel).filter(AccessLevel.levelRank == level_rank).first()

def create_access_level(db: Session, data: AccessLevelCreate, new_id: str, current_user: dict):
    created_by = current_user["userId"]
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

    updated_data = {
        "id": db_obj.id,
        "code": db_obj.code,
        "levelRank": db_obj.levelRank,
        "levelName": db_obj.levelName,
        "description": db_obj.description,
        "isSystem": db_obj.isSystem,
    }

    log_crud_action(
        action=ActionType.CREATE,
        user=created_by,
        user_full_name=current_user["fullName"],
        role=current_user["roleName"],
        entity_id=new_id,
        table='access_level',
        message=f"Created access level: {db_obj.levelName}",
        updated_data=updated_data,
    )

    return db_obj

def update_access_level(db: Session, db_obj: AccessLevel, data: AccessLevelUpdate, current_user: dict):
    modified_by = current_user["userId"]
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

    original_data = {field: getattr(db_obj, field) for field in update_data.keys()}

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db_obj.modifiedById = modified_by
    db.commit()
    db.refresh(db_obj)

    updated_data = {field: getattr(db_obj, field) for field in original_data.keys()}

    log_crud_action(
        action=ActionType.UPDATE,
        user=modified_by,
        user_full_name=current_user["fullName"],
        role=current_user["roleName"],
        entity_id=db_obj.id,
        table='access_level',
        message=f"Updated access level: {db_obj.levelName}",
        original_data=original_data,
        updated_data=updated_data,
    )

    return db_obj

def delete_access_level(db: Session, db_obj: AccessLevel, current_user: dict):
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

    original_data = {
        "id": db_obj.id,
        "code": db_obj.code,
        "levelRank": db_obj.levelRank,
        "levelName": db_obj.levelName,
        "description": db_obj.description,
    }

    db.delete(db_obj)
    db.commit()

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user["userId"],
        user_full_name=current_user["fullName"],
        role=current_user["roleName"],
        entity_id=original_data["id"],
        table='access_level',
        message=f"Deleted access level: {original_data['levelName']}",
        original_data=original_data,
    )