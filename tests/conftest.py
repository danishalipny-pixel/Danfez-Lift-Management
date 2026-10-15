import pytest
from backend.app.database import engine, Base, SessionLocal, init_db
from backend.app.services.seed_data import seed_database
from backend.app.services.simulator_engine import simulator_manager
from backend.app.models.elevator import Elevator

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    seed_database(db)
    elevators = db.query(Elevator).all()
    for e in elevators:
        simulator_manager.get_or_create(e.id, e.floor_count, e.current_floor)
    db.close()
    yield
