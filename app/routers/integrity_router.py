from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.admin_config_model import AdminConfig
from app.database import get_db


router = APIRouter()

@router.get("/adminconfig")
async def get_admin_config(
    hours_back: int = Query(1, ge=1, le=168, description="Hours to look back (1-168)"),
    limit: int = Query(1000, ge=1, le=5000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Returns userconfig and their last modified timestamps.
    Used by reconciliation service to detect data drift.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        adminconfigs = db.query(AdminConfig).filter(
            AdminConfig.modifiedDate >= cutoff_time
        ).order_by(AdminConfig.id).limit(limit).offset(offset).all()
        
        records = []
        for adminconfig in adminconfigs:
            records.append({
                "id": adminconfig.id,
                "modified_date": adminconfig.modifiedDate.isoformat(),
                "version_timestamp": int(adminconfig.modifiedDate.timestamp() * 1000),
                "record_type": "adminconfig"
            })
        
        # Get total count for pagination
        total_count = db.query(AdminConfig).filter(
            AdminConfig.modifiedDate >= cutoff_time
        ).count()
        
        return {
            "service": "adminconfig",
            "endpoint": "/integrity/adminconfig",
            "window_hours": hours_back,
            "cutoff_time": cutoff_time.isoformat(),
            "total_count": total_count,
            "returned_count": len(records),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(records)) < total_count,
            "records": records,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patient integrity check failed: {str(e)}")
    

@router.get("/summary")
async def get_integrity_summary(
    hours_back: int = Query(1, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Returns a summary of all user-related record counts for the specified time window.
    Useful for high-level drift detection and monitoring.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Count records in each table
        adminconfig_count = db.query(AdminConfig).filter(
            AdminConfig.modifiedDate >= cutoff_time
        ).count()
        

        return {
            "service": "user",
            "endpoint": "/integrity/summary",
            "window_hours": hours_back,
            "cutoff_time": cutoff_time.isoformat(),
            "record_counts": {
                "adminconfig": adminconfig_count,
                "total": adminconfig_count
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integrity summary failed: {str(e)}")


# Health check endpoint for the integrity system
@router.get("/health")
async def integrity_health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify integrity system is working.
    """
    try:
        # Test database connectivity
        db.execute(text("SELECT 1"))
        
        # Get recent adminconfig to verify data access
        recent_adminconfig = db.query(AdminConfig).filter(
            AdminConfig.modifiedDate >= datetime.now() - timedelta(hours=24)
        ).first()
        
        return {
            "status": "healthy",
            "service": "adminconfig",
            "database_connected": True,
            "recent_data_available": recent_adminconfig is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Integrity health check failed: {str(e)}")
