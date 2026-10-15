import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    resp = client.post("/api/auth/login", json={
        "email": "admin@danfez.com",
        "password": "DanfezAdmin2026!"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_fault_lifecycle(auth_headers):
    # 1. Log a test fault
    fault_payload = {
        "elevator_id": 1,
        "severity": "High",
        "category": "Motor Drive",
        "description": "Drive overheating alarm triggered during heavy traffic."
    }
    create_resp = client.post("/api/faults/", json=fault_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    fault = create_resp.json()
    fault_id = fault["id"]
    assert fault["is_acknowledged"] is False
    assert fault["is_resolved"] is False

    # 2. Acknowledge fault and assign tech
    ack_resp = client.post(f"/api/faults/{fault_id}/acknowledge", json={"assigned_technician_id": 1}, headers=auth_headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["is_acknowledged"] is True
    assert ack_resp.json()["assigned_technician_id"] == 1

    # 3. Resolve fault
    res_resp = client.post(f"/api/faults/{fault_id}/resolve", json={"resolution_notes": "Cleaned cabinet cooling fans and verified motor temp 42C."}, headers=auth_headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["is_resolved"] is True
    assert res_resp.json()["resolved_at"] is not None

def test_reports_and_csv_export(auth_headers):
    dash_resp = client.get("/api/reports/dashboard", headers=auth_headers)
    assert dash_resp.status_code == 200
    d = dash_resp.json()
    assert "total_elevators" in d
    assert "elevators_operational" in d
    assert "active_faults" in d

    # Export tickets CSV
    csv_resp = client.get("/api/reports/export/tickets", headers=auth_headers)
    assert csv_resp.status_code == 200
    assert "Ticket Number" in csv_resp.text
