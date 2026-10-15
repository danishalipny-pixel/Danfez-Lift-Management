import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from ..database import SessionLocal
from ..models.elevator import Elevator
from ..models.fault import FaultAlert

class ElevatorSimulator:
    def __init__(self, elevator_id: int, floor_count: int = 10, current_floor: int = 1):
        self.elevator_id = elevator_id
        self.floor_count = floor_count
        self.current_floor = current_floor
        self.target_floor = current_floor
        self.direction = "idle" # "up", "down", "idle"
        self.door_state = "closed" # "closed", "opening", "open", "closing"
        self.status = "operational" # "operational", "moving", "idle", "maintenance", "fault"
        self.speed_multiplier = 1.0 # 0.5, 1.0, 2.0, 5.0
        self.emergency_stopped = False
        self.request_queue: List[int] = []
        self.door_timer = 0
        self.events: List[dict] = []
        self.add_event("SYSTEM", f"Elevator simulator initialized at Floor {current_floor}")

    def add_event(self, event_type: str, message: str):
        event = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "type": event_type,
            "message": message,
            "floor": self.current_floor
        }
        self.events.insert(0, event)
        if len(self.events) > 50:
            self.events.pop()

    def add_floor_request(self, floor: int) -> bool:
        if self.emergency_stopped or self.status == "maintenance":
            self.add_event("WARNING", f"Cannot request Floor {floor}: Elevator is in {self.status} state")
            return False
        
        if floor < 1 or floor > self.floor_count:
            return False

        # If already on this floor and idle
        if floor == self.current_floor:
            if self.door_state in ("closed", "closing"):
                self.door_state = "opening"
                self.door_timer = 3
                self.add_event("DOOR", f"Opening doors at current Floor {floor}")
            return True

        if floor not in self.request_queue:
            self.request_queue.append(floor)
            self.add_event("CALL", f"Call registered for Floor {floor}")
            
            if self.direction == "idle":
                self.update_next_target()
            return True
        return False

    def update_next_target(self):
        if not self.request_queue:
            self.direction = "idle"
            self.status = "operational" if not self.emergency_stopped else "fault"
            return

        # Directional algorithm (LOOK/SCAN)
        if self.direction == "up":
            # Higher floors first
            above = [f for f in self.request_queue if f > self.current_floor]
            if above:
                self.target_floor = min(above)
            else:
                # Switch direction downwards
                self.direction = "down"
                self.target_floor = max(self.request_queue)
        elif self.direction == "down":
            below = [f for f in self.request_queue if f < self.current_floor]
            if below:
                self.target_floor = max(below)
            else:
                self.direction = "up"
                self.target_floor = min(self.request_queue)
        else: # idle
            # Pick closest
            self.target_floor = min(self.request_queue, key=lambda f: abs(f - self.current_floor))
            if self.target_floor > self.current_floor:
                self.direction = "up"
            elif self.target_floor < self.current_floor:
                self.direction = "down"
            else:
                self.direction = "idle"

    def trigger_door_action(self, action: str):
        if self.emergency_stopped or self.status == "moving":
            return False
        if action == "open":
            self.door_state = "opening"
            self.door_timer = 3
            self.add_event("DOOR", f"Manual door open requested at Floor {self.current_floor}")
            return True
        elif action == "close":
            if self.door_state in ("open", "opening"):
                self.door_state = "closing"
                self.door_timer = 2
                self.add_event("DOOR", f"Manual door close requested at Floor {self.current_floor}")
                return True
        return False

    def trigger_emergency_stop(self):
        self.emergency_stopped = True
        self.status = "fault"
        self.direction = "idle"
        self.add_event("CRITICAL", f"EMERGENCY STOP ENGAGED at Floor {self.current_floor}. Simulation halted.")

    def reset_simulator(self):
        self.emergency_stopped = False
        self.status = "operational"
        self.direction = "idle"
        self.door_state = "closed"
        self.current_floor = 1
        self.target_floor = 1
        self.request_queue = []
        self.door_timer = 0
        self.add_event("SYSTEM", "Elevator reset to Floor 1. All queues cleared.")

    def tick(self):
        """Simulate one state transition tick."""
        if self.emergency_stopped or self.status == "maintenance":
            return

        # 1. Handle Door states
        if self.door_state == "opening":
            self.door_timer -= 1
            if self.door_timer <= 0:
                self.door_state = "open"
                self.door_timer = 4 # Hold open for 4 ticks
                self.add_event("DOOR", f"Doors fully open at Floor {self.current_floor}")
            return

        if self.door_state == "open":
            self.door_timer -= 1
            if self.door_timer <= 0:
                self.door_state = "closing"
                self.door_timer = 2
                self.add_event("DOOR", f"Doors closing at Floor {self.current_floor}")
            return

        if self.door_state == "closing":
            self.door_timer -= 1
            if self.door_timer <= 0:
                self.door_state = "closed"
                self.add_event("DOOR", f"Doors closed at Floor {self.current_floor}")
                self.update_next_target()
            return

        # 2. If doors are closed, can move
        if self.door_state == "closed":
            if not self.request_queue:
                self.direction = "idle"
                self.status = "operational"
                return

            self.update_next_target()

            if self.current_floor < self.target_floor:
                self.direction = "up"
                self.status = "moving"
                self.current_floor += 1
                self.add_event("MOVE", f"Passing Floor {self.current_floor} (Ascending to {self.target_floor})")
            elif self.current_floor > self.target_floor:
                self.direction = "down"
                self.status = "moving"
                self.current_floor -= 1
                self.add_event("MOVE", f"Passing Floor {self.current_floor} (Descending to {self.target_floor})")

            # Check if arrived at a requested floor
            if self.current_floor in self.request_queue:
                self.request_queue.remove(self.current_floor)
                self.status = "idle"
                self.door_state = "opening"
                self.door_timer = 2
                self.add_event("ARRIVAL", f"🔔 Arrived at Floor {self.current_floor}. Opening doors.")
                if not self.request_queue:
                    self.direction = "idle"

    def to_dict(self) -> dict:
        return {
            "id": self.elevator_id,
            "current_floor": self.current_floor,
            "target_floor": self.target_floor,
            "direction": self.direction,
            "door_state": self.door_state,
            "status": self.status,
            "speed_multiplier": self.speed_multiplier,
            "emergency_stopped": self.emergency_stopped,
            "request_queue": sorted(list(self.request_queue)),
            "floor_count": self.floor_count,
            "events": self.events[:25],
            "is_simulation": True
        }


class SimulatorManager:
    def __init__(self):
        self.simulators: Dict[int, ElevatorSimulator] = {}
        self.active_websockets: Set[WebSocket] = set()
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def get_or_create(self, elevator_id: int, floor_count: int = 10, current_floor: int = 1) -> ElevatorSimulator:
        if elevator_id not in self.simulators:
            self.simulators[elevator_id] = ElevatorSimulator(
                elevator_id=elevator_id,
                floor_count=floor_count,
                current_floor=current_floor
            )
        return self.simulators[elevator_id]

    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def broadcast_state(self):
        if not self.active_websockets:
            return
        data = {
            "type": "SIMULATOR_UPDATE",
            "elevators": {eid: sim.to_dict() for eid, sim in self.simulators.items()}
        }
        dead_connections = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead_connections.add(ws)
        for ws in dead_connections:
            self.active_websockets.discard(ws)

    def sync_to_db(self):
        """Persist current simulator position and status to DB."""
        try:
            db = SessionLocal()
            for eid, sim in self.simulators.items():
                elev = db.query(Elevator).filter(Elevator.id == eid).first()
                if elev:
                    elev.current_floor = sim.current_floor
                    elev.target_floor = sim.target_floor
                    elev.direction = sim.direction
                    elev.door_state = sim.door_state
                    elev.status = sim.status
                    elev.emergency_stopped = sim.emergency_stopped
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error syncing simulator state to DB: {e}")

    async def run_loop(self):
        self.running = True
        tick_counter = 0
        while self.running:
            try:
                # Default tick every 0.8s
                await asyncio.sleep(0.8)
                tick_counter += 1
                for sim in list(self.simulators.values()):
                    sim.tick()
                
                await self.broadcast_state()

                # Sync to database every 5 ticks to keep DB accurate
                if tick_counter % 5 == 0:
                    self.sync_to_db()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in simulator loop: {e}")
                await asyncio.sleep(1.0)

    def start(self):
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self.run_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

simulator_manager = SimulatorManager()
