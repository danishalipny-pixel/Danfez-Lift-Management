from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/api/health", tags=["Health Check"])

@router.get("")
@router.get("/")
def health_check(db: Session = Depends(get_db)):
    db_connected = True
    try:
        from ..models.building import Building
        db.query(Building).first()
    except Exception:
        db_connected = False

    return {
        "status": "healthy" if db_connected else "degraded",
        "system": "Danfez Lift Control API",
        "version": "2.0.0",
        "database_connected": db_connected,
        "mode": "Simulation / Development",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
