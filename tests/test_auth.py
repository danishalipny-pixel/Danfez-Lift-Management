import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["system"] == "Danfez Lift Control API"

def test_login_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@danfez.com",
        "password": "DanfezAdmin2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["email"] == "admin@danfez.com"

def test_login_technician():
    response = client.post("/api/auth/login", json={
        "email": "tech@danfez.com",
        "password": "DanfezTech2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "technician"

def test_login_viewer():
    response = client.post("/api/auth/login", json={
        "email": "viewer@danfez.com",
        "password": "DanfezView2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "viewer"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "admin@danfez.com",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401

def test_rbac_user_management():
    # 1. Viewer trying to fetch users list -> should be 403 Forbidden
    viewer_login = client.post("/api/auth/login", json={
        "email": "viewer@danfez.com",
        "password": "DanfezView2026!"
    }).json()
    viewer_token = viewer_login["access_token"]
    
    resp_viewer = client.get("/api/users/", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp_viewer.status_code == 403

    # 2. Admin trying to fetch users list -> should be 200 OK
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@danfez.com",
        "password": "DanfezAdmin2026!"
    }).json()
    admin_token = admin_login["access_token"]

    resp_admin = client.get("/api/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) >= 3
