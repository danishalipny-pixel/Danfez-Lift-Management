from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.elevator import Elevator
from ..models.fault import FaultAlert
from ..models.user import User
from ..schemas.elevator import (
    SimulatorCallRequest, SimulatorDoorRequest, SimulatorSpeedRequest, SimulatorTestFaultRequest
)
from ..auth.dependencies import get_current_user, get_optional_current_user, require_technician_or_admin
from ..services.simulator_engine import simulator_manager
from ..services.audit_service import log_audit

router = APIRouter(prefix="/api/simulator", tags=["Elevator Simulator"])

@router.websocket("/ws")
async def websocket_simulator_feed(websocket: WebSocket):
    """Real-time WebSocket telemetry feed for elevator simulator animations."""
    await simulator_manager.connect_ws(websocket)
    try:
        # Send initial full state immediately upon connection
        await websocket.send_json({
            "type": "INIT_STATE",
            "elevators": {eid: sim.to_dict() for eid, sim in simulator_manager.simulators.items()}
        })
        while True:
            # Keep connection open, handle incoming client ping or requests if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        simulator_manager.disconnect_ws(websocket)
    except Exception:
        simulator_manager.disconnect_ws(websocket)

@router.get("/{elevator_id}/status")
def get_simulator_status(elevator_id: int, db: Session = Depends(get_db)):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")
    
    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    state = sim.to_dict()
    state["elevator_name"] = elev.name
    state["elevator_code"] = elev.code
    state["building_name"] = elev.building.name if elev.building else "Main Building"
    return state

@router.post("/{elevator_id}/call")
async def call_floor(
    elevator_id: int,
    call_req: SimulatorCallRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    
    if call_req.floor < 1 or call_req.floor > sim.floor_count:
        raise HTTPException(
            status_code=400,
            detail=f"Floor {call_req.floor} is invalid. Valid floors are 1 to {sim.floor_count}."
        )

    success = sim.add_floor_request(call_req.floor)
    await simulator_manager.broadcast_state()

    user_id = current_user.id if current_user else 1
    user_email = current_user.email if current_user else "dispatcher@danfez.com"
    log_audit(
        db, action="SIM_CALL_FLOOR", resource=f"Elevator:{elevator_id}",
        user_id=user_id, user_email=user_email,
        details=f"User called Floor {call_req.floor} on {elev.code}"
    )

    return {
        "success": success,
        "floor": call_req.floor,
        "message": f"Floor {call_req.floor} registered in request queue",
        "current_floor": sim.current_floor,
        "queue": sim.request_queue
    }

@router.post("/{elevator_id}/door")
async def door_action(
    elevator_id: int,
    door_req: SimulatorDoorRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    action_lower = door_req.action.lower()
    if action_lower not in ("open", "close"):
        raise HTTPException(status_code=400, detail="Action must be 'open' or 'close'")

    success = sim.trigger_door_action(action_lower)
    await simulator_manager.broadcast_state()

    user_id = current_user.id if current_user else 1
    user_email = current_user.email if current_user else "dispatcher@danfez.com"
    log_audit(
        db, action="SIM_DOOR_ACTION", resource=f"Elevator:{elevator_id}",
        user_id=user_id, user_email=user_email,
        details=f"Door {action_lower} requested on {elev.code}"
    )

    return {"success": success, "door_state": sim.door_state}

@router.post("/{elevator_id}/emergency-stop")
async def emergency_stop(
    elevator_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    sim.trigger_emergency_stop()
    await simulator_manager.broadcast_state()

    # Log critical audit
    user_id = current_user.id if current_user else 1
    user_email = current_user.email if current_user else "dispatcher@danfez.com"
    log_audit(
        db, action="EMERGENCY_STOP_TRIGGERED", resource=f"Elevator:{elevator_id}",
        user_id=user_id, user_email=user_email,
        details=f"Simulated EMERGENCY STOP engaged on {elev.code} at Floor {sim.current_floor}"
    )

    import uuid
    critical_fault = FaultAlert(
        fault_code=f"FLT-ESTOP-{elevator_id}-{uuid.uuid4().hex[:6].upper()}",
        elevator_id=elevator_id,
        severity="Critical",
        category="Safety Circuit",
        description=f"SIMULATED EMERGENCY STOP: Emergency stop switch actuated on {elev.code} cabin at Floor {sim.current_floor}. Software simulation halted.",
        is_acknowledged=False,
        is_resolved=False
    )
    db.add(critical_fault)
    elev.status = "fault"
    elev.emergency_stopped = True
    db.commit()

    return {
        "message": "Simulated emergency stop engaged. Elevator halted.",
        "status": sim.status,
        "floor": sim.current_floor,
        "warning": "SOFTWARE SIMULATION ONLY. In an actual building emergency, follow certified building evacuation and safety protocols."
    }

@router.post("/{elevator_id}/reset")
async def reset_simulator(
    elevator_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    sim.reset_simulator()

    elev.current_floor = 1
    elev.target_floor = 1
    elev.status = "operational"
    elev.direction = "idle"
    elev.door_state = "closed"
    elev.emergency_stopped = False
    db.commit()

    await simulator_manager.broadcast_state()

    user_id = current_user.id if current_user else 1
    user_email = current_user.email if current_user else "dispatcher@danfez.com"
    log_audit(
        db, action="SIMULATOR_RESET", resource=f"Elevator:{elevator_id}",
        user_id=user_id, user_email=user_email,
        details=f"Elevator {elev.code} reset to Floor 1 by {user_email}"
    )

    return {"message": "Simulator reset to Floor 1 successfully", "status": sim.status}

@router.post("/{elevator_id}/speed")
async def set_speed(
    elevator_id: int,
    speed_req: SimulatorSpeedRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    if speed_req.speed_multiplier not in (0.5, 1.0, 2.0, 5.0):
        raise HTTPException(status_code=400, detail="Allowed speeds: 0.5, 1.0, 2.0, 5.0")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    sim.speed_multiplier = speed_req.speed_multiplier
    elev.speed_multiplier = speed_req.speed_multiplier
    db.commit()

    sim.add_event("CONFIG", f"Simulation speed adjusted to {speed_req.speed_multiplier}x")
    await simulator_manager.broadcast_state()

    return {"speed_multiplier": sim.speed_multiplier}

@router.post("/{elevator_id}/test-fault")
async def inject_test_fault(
    elevator_id: int,
    fault_req: SimulatorTestFaultRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
    if not elev:
        raise HTTPException(status_code=404, detail="Elevator not found")

    sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)

    import uuid
    fault_code = f"FLT-SIM-{uuid.uuid4().hex[:6].upper()}"
    fault = FaultAlert(
        fault_code=fault_code,
        elevator_id=elevator_id,
        severity=fault_req.severity,
        category=fault_req.category,
        description=f"[SIMULATION TEST] {fault_req.description}",
        is_acknowledged=False,
        is_resolved=False
    )
    db.add(fault)

    if fault_req.severity in ("High", "Critical"):
        sim.status = "fault"
        elev.status = "fault"
    
    sim.add_event("FAULT", f"Simulated {fault_req.severity} fault injected: {fault_req.category}")
    db.commit()
    db.refresh(fault)

    await simulator_manager.broadcast_state()

    user_id = current_user.id if current_user else 1
    user_email = current_user.email if current_user else "dispatcher@danfez.com"
    log_audit(
        db, action="TEST_FAULT_INJECTED", resource=f"Elevator:{elevator_id}",
        user_id=user_id, user_email=user_email,
        details=f"Injected test fault {fault.fault_code} ({fault_req.severity})"
    )

    return {
        "message": f"Simulated fault {fault.fault_code} injected successfully",
        "fault_id": fault.id,
        "severity": fault.severity
    }

@router.get("/{elevator_id}/events")
def get_elevator_events(elevator_id: int, db: Session = Depends(get_db)):
    sim = simulator_manager.simulators.get(elevator_id)
    if not sim:
        elev = db.query(Elevator).filter(Elevator.id == elevator_id).first()
        if not elev:
            raise HTTPException(status_code=404, detail="Elevator not found")
        sim = simulator_manager.get_or_create(elev.id, elev.floor_count, elev.current_floor)
    return sim.events
