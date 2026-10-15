from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.building import Building
from ..models.elevator import Elevator
from ..models.user import User
from ..schemas.building import BuildingCreate, BuildingResponse
from ..auth.dependencies import get_current_user, get_optional_current_user, require_admin
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/buildings", tags=["Buildings"])

@router.get("/", response_model=List[BuildingResponse])
def get_buildings(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    buildings = db.query(Building).all()
    results = []
    for b in buildings:
        count = db.query(Elevator).filter(Elevator.building_id == b.id).count()
        results.append(BuildingResponse(
            id=b.id,
            name=b.name,
            address=b.address,
            total_floors=b.total_floors,
            created_at=b.created_at,
            elevator_count=count
        ))
    return results

@router.post("/", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
def create_building(
    b_in: BuildingCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    building = Building(
        name=b_in.name,
        address=b_in.address,
        total_floors=b_in.total_floors
    )
    db.add(building)
    db.commit()
    db.refresh(building)

    log_audit(
        db, action="BUILDING_CREATED", resource=f"Building:{building.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Created building {building.name}"
    )
    return BuildingResponse(
        id=building.id,
        name=building.name,
        address=building.address,
        total_floors=building.total_floors,
        created_at=building.created_at,
        elevator_count=0
    )

@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    b = db.query(Building).filter(Building.id == building_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Building not found")
    count = db.query(Elevator).filter(Elevator.building_id == b.id).count()
    return BuildingResponse(
        id=b.id,
        name=b.name,
        address=b.address,
        total_floors=b.total_floors,
        created_at=b.created_at,
        elevator_count=count
    )
