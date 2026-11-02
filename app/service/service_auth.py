import os
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db

_optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login", auto_error=False)


def get_optional_current_user(
    token: Optional[str] = Depends(_optional_oauth2),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    if not token:
        return None
    from ..service import user_auth_service as AuthService
    try:
        return AuthService.get_current_user(token=token, db=db)
    except HTTPException:
        return None


def verify_service_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> None:
    service_key = os.environ.get("INTERNAL_SERVICE_API_KEY")
    if not service_key:
        raise HTTPException(status_code=500, detail="Service API key not configured.")
    if x_api_key != service_key:
        raise HTTPException(status_code=403, detail="Invalid service API key.")
