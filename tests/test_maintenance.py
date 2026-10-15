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

def test_maintenance_tickets_crud(auth_headers):
    # 1. Create a ticket
    ticket_payload = {
        "elevator_id": 1,
        "category": "Door Sensor",
        "priority": "High",
        "status": "Open",
        "description": "Optical sensor intermittently false-tripping at floor 3."
    }
    create_resp = client.post("/api/maintenance/", json=ticket_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    created_ticket = create_resp.json()
    assert created_ticket["ticket_number"].startswith("MNT-2026-")
    ticket_id = created_ticket["id"]

    # 2. Update status and assign technician
    update_payload = {
        "status": "In Progress",
        "assigned_technician_id": 1
    }
    update_resp = client.put(f"/api/maintenance/{ticket_id}", json=update_payload, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "In Progress"
    assert update_resp.json()["assigned_technician_id"] == 1

    # 3. Resolve ticket
    resolve_payload = {
        "status": "Resolved",
        "resolution_notes": "Cleaned lens and recalibrated optical safety edge."
    }
    resolve_resp = client.put(f"/api/maintenance/{ticket_id}", json=resolve_payload, headers=auth_headers)
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "Resolved"
    assert resolve_resp.json()["completion_date"] is not None

    # 4. Search and filter
    list_resp = client.get("/api/maintenance/?status=Resolved", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(t["id"] == ticket_id for t in list_resp.json())
