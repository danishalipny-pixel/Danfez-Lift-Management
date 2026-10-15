import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

PAGES = [
    "/",
    "/index.html",
    "/login.html",
    "/dashboard.html",
    "/lifts.html",
    "/simulator.html",
    "/maintenance.html",
    "/alerts.html",
    "/technicians.html",
    "/reports.html",
    "/users.html",
    "/settings.html",
    "/profile.html",
    "/offline.html",
    "/manifest.json",
    "/service-worker.js"
]

@pytest.mark.parametrize("page", PAGES)
def test_frontend_routes_served(page):
    response = client.get(page)
    assert response.status_code == 200, f"Page {page} returned status {response.status_code}"
    assert len(response.content) > 50

def test_static_assets():
    resp_css = client.get("/assets/css/danfez-theme.css")
    assert resp_css.status_code == 200

    resp_api = client.get("/assets/js/api.js")
    assert resp_api.status_code == 200

    resp_logo = client.get("/assets/icons/danfez-logo.svg")
    assert resp_logo.status_code == 200
