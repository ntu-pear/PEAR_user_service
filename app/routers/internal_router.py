from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..service.service_auth import verify_service_api_key
from ..models.user_model import User
from ..rate_limiter import TokenBucket, rate_limit

global_bucket = TokenBucket(rate=5, capacity=10)

router = APIRouter(
    tags=["internal"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/internal/user/check-nric/{nric}")
@rate_limit(global_bucket, tokens_required=1)
def check_nric(
    nric: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_service_api_key),
):
    user = db.query(User).filter(
        User.nric == nric,
        User.isDeleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="NRIC not found")
    return {"found": True}
