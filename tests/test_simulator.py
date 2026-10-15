import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.simulator_engine import simulator_manager

client = TestClient(app)

@pytest.fixture
def auth_headers():
    resp = client.post("/api/auth/login", json={
        "email": "admin@danfez.com",
        "password": "DanfezAdmin2026!"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_simulator_call_and_movement(auth_headers):
    # Reset elevator 1 first
    client.post("/api/simulator/1/reset", headers=auth_headers)
    
    # Check initial status
    status_resp = client.get("/api/simulator/1/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["current_floor"] == 1
    assert data["door_state"] == "closed"
    assert data["is_simulation"] is True

    # Call floor 5
    call_resp = client.post("/api/simulator/1/call", json={"floor": 5}, headers=auth_headers)
    assert call_resp.status_code == 200
    assert 5 in call_resp.json()["queue"]

    # Run simulator ticks directly to verify state machine
    sim = simulator_manager.get_or_create(1)
    for _ in range(8):
        sim.tick()
    
    assert sim.current_floor > 1

def test_simulator_emergency_stop_and_reset(auth_headers):
    # Trigger emergency stop
    stop_resp = client.post("/api/simulator/1/emergency-stop", headers=auth_headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "fault"
    assert "SOFTWARE SIMULATION ONLY" in stop_resp.json()["warning"]

    # Verify calls are blocked during emergency stop
    blocked_call = client.post("/api/simulator/1/call", json={"floor": 4}, headers=auth_headers)
    assert blocked_call.json()["success"] is False

    # Reset
    reset_resp = client.post("/api/simulator/1/reset", headers=auth_headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "operational"

    status_resp = client.get("/api/simulator/1/status")
    assert status_resp.json()["current_floor"] == 1
    assert status_resp.json()["emergency_stopped"] is False
