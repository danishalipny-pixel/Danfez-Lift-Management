from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.elevator import Elevator
from ..models.building import Building
from ..models.user import User
from ..schemas.elevator import ElevatorCreate, ElevatorUpdate, ElevatorResponse
from ..auth.dependencies import get_current_user, get_optional_current_user, require_admin
from ..services.simulator_engine import simulator_manager
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/elevators", tags=["Elevators"])

@router.get("/", response_model=List[ElevatorResponse])
def get_elevators(db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    elevators = db.query(Elevator).all()
    results = []
    for elev in elevators:
        # Merge live simulator state if present
        sim = simulator_manager.simulators.get(elev.id)
        current_floor = sim.current_floor if sim else elev.current_floor
        target_floor = sim.target_floor if sim else elev.target_floor
        status_val = sim.status if sim else elev.status
        direction_val = sim.direction if sim else elev.direction
        door_val = sim.door_state if sim else elev.door_state
        emergency_stopped = sim.emergency_stopped if sim else elev.emergency_stopped
        queue_val = list(sim.request_queue) if sim else []
        speed = sim.speed_multiplier if sim else elev.speed_multiplier

        results.append(ElevatorResponse(
            id=elev.id,
            name=elev.name,
            code=elev.code,
            building_id=elev.building_id,
            floor_count=elev.floor_count,
            speed_multiplier=speed,
            current_floor=current_floor,
            target_floor=target_floor,
            status=status_val,
            direction=direction_val,
            door_state=door_val,
            emergency_stopped=emergency_stopped,
            building_name=elev.building.name if elev.building else "Unassigned",
            last_maintenance_date=elev.last_maintenance_date,
            created_at=elev.created_at,
            updated_at=elev.updated_at,
            request_queue=queue_val
        ))
    return results

@router.post("/", response_model=ElevatorResponse, status_code=status.HTTP_201_CREATED)
def create_elevator(
    elev_in: ElevatorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    building = db.query(Building).filter(Building.id == elev_in.building_id).first()
    if not building:
        raise HTTPException(status_code=400, detail="Referenced building does not exist")

    existing = db.query(Elevator).filter(Elevator.code == elev_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="An elevator with this code already exists")

    elevator = Elevator(
        name=elev_in.name,
        code=elev_in.code,
        building_id=elev_in.building_id,
        floor_count=elev_in.floor_count,
        speed_multiplier=elev_in.speed_multiplier,
        current_floor=1,
        target_floor=1,
        status="operational",
        direction="idle",
        door_state="closed"
    )
    db.add(elevator)
    db.commit()
    db.refresh(elevator)

    # Initialize in simulator manager
    simulator_manager.get_or_create(elevator.id, elevator.floor_count, 1)

    log_audit(
        db, action="ELEVATOR_CREATED", resource=f"Elevator:{elevator.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Created simulated elevator {elevator.code} ({elevator.name})"
    )

    return ElevatorResponse(
        id=elevator.id,
        name=elevator.name,
        code=elevator.code,
        building_id=elevator.building_id,
        floor_count=elevator.floor_count,
        speed_multiplier=elevator.speed_multiplier,
        current_floor=elevator.current_floor,
        target_floor=elevator.target_floor,
        status=elevator.status,
        direction=elevator.direction,
        door_state=elevator.door_state,
        emergency_stopped=elevator.emergency_stopped,
        building_name=building.name,
        last_maintenance_date=elevator.last_maintenance_date,
        created_at=elevator.created_at,
        updated_at=elevator.updated_at,
        request_queue=[]
    )

@router.get("/{elevator_id}", response_model=ElevatorResponse)
def get_elevator(elevator_id: int, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.simulators.get(elev.id)
    return ElevatorResponse(
        id=elev.id,
        name=elev.name,
        code=elev.code,
        building_id=elev.building_id,
        floor_count=elev.floor_count,
        speed_multiplier=sim.speed_multiplier if sim else elev.speed_multiplier,
        current_floor=sim.current_floor if sim else elev.current_floor,
        target_floor=sim.target_floor if sim else elev.target_floor,
        status=sim.status if sim else elev.status,
        direction=sim.direction if sim else elev.direction,
        door_state=sim.door_state if sim else elev.door_state,
        emergency_stopped=sim.emergency_stopped if sim else elev.emergency_stopped,
        building_name=elev.building.name if elev.building else "Unassigned",
        last_maintenance_date=elev.last_maintenance_date,
        created_at=elev.created_at,
        updated_at=elev.updated_at,
        request_queue=list(sim.request_queue) if sim else []
    )

@router.put("/{elevator_id}", response_model=ElevatorResponse)
def update_elevator(
    elevator_id: int,
    elev_update: ElevatorUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    if elev_update.name is not None:
        elev.name = elev_update.name
    if elev_update.code is not None:
        elev.code = elev_update.code
    if elev_update.floor_count is not None:
        elev.floor_count = elev_update.floor_count
        sim = simulator_manager.simulators.get(elev.id)
        if sim:
            sim.floor_count = elev_update.floor_count
    if elev_update.status is not None:
        elev.status = elev_update.status
        sim = simulator_manager.simulators.get(elev.id)
        if sim:
            sim.status = elev_update.status
    if elev_update.speed_multiplier is not None:
        elev.speed_multiplier = elev_update.speed_multiplier
        sim = simulator_manager.simulators.get(elev.id)
        if sim:
            sim.speed_multiplier = elev_update.speed_multiplier

    db.commit()
    db.refresh(elev)

    log_audit(
        db, action="ELEVATOR_UPDATED", resource=f"Elevator:{elev.id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Updated simulated elevator {elev.code}"
    )

    sim = simulator_manager.simulators.get(elev.id)
    return ElevatorResponse(
        id=elev.id,
        name=elev.name,
        code=elev.code,
        building_id=elev.building_id,
        floor_count=elev.floor_count,
        speed_multiplier=sim.speed_multiplier if sim else elev.speed_multiplier,
        current_floor=sim.current_floor if sim else elev.current_floor,
        target_floor=sim.target_floor if sim else elev.target_floor,
        status=sim.status if sim else elev.status,
        direction=sim.direction if sim else elev.direction,
        door_state=sim.door_state if sim else elev.door_state,
        emergency_stopped=sim.emergency_stopped if sim else elev.emergency_stopped,
        building_name=elev.building.name if elev.building else "Unassigned",
        last_maintenance_date=elev.last_maintenance_date,
        created_at=elev.created_at,
        updated_at=elev.updated_at,
        request_queue=list(sim.request_queue) if sim else []
    )

@router.delete("/{elevator_id}")
def delete_elevator(
    elevator_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    code = elev.code
    db.delete(elev)
    db.commit()

    if elevator_id in simulator_manager.simulators:
        del simulator_manager.simulators[elevator_id]

    log_audit(
        db, action="ELEVATOR_DELETED", resource=f"Elevator:{elevator_id}",
        user_id=current_admin.id, user_email=current_admin.email,
        details=f"Deleted simulated elevator {code}"
    )
    return {"message": f"Elevator {code} deleted successfully"}
