import requests

BASE = "http://localhost:8000"

def run_checks():
    # 1. Health check
    r = requests.get(f"{BASE}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print("1. Health check passed:", r.json())

    # 2. Login admin
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@danfez.com", "password": "DanfezAdmin2026!"})
    assert r.status_code == 200, f"Login failed: {r.status_code}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("2. Admin login passed, token received.")

    # 3. Dashboard summary
    r = requests.get(f"{BASE}/api/reports/dashboard", headers=headers)
    assert r.status_code == 200
    dash = r.json()
    print(f"3. Dashboard summary passed: Total Elevators={dash['total_elevators']}, Operational={dash['elevators_operational']}, Availability={dash['availability_rate']}%, Active Faults={dash['active_faults']}")

    # 4. Elevator 1 Simulator status
    r = requests.get(f"{BASE}/api/simulator/1/status", headers=headers)
    assert r.status_code == 200
    sim = r.json()
    print(f"4. Simulator status passed: Floor {sim['current_floor']}, Direction: {sim['direction']}, Doors: {sim['door_state']}")

    # 5. Call floor 7
    r = requests.post(f"{BASE}/api/simulator/1/call", json={"floor": 7}, headers=headers)
    assert r.status_code == 200
    print("5. Simulator call to Floor 7 registered in queue:", r.json()["queue"])

    # 6. Maintenance tickets
    r = requests.get(f"{BASE}/api/maintenance/", headers=headers)
    assert r.status_code == 200
    tickets = r.json()
    print(f"6. Maintenance tickets retrieved: {len(tickets)} tickets.")

    # 7. Faults
    r = requests.get(f"{BASE}/api/faults/", headers=headers)
    assert r.status_code == 200
    faults = r.json()
    print(f"7. Fault alerts retrieved: {len(faults)} alerts.")

    # 8. Technicians
    r = requests.get(f"{BASE}/api/technicians/", headers=headers)
    assert r.status_code == 200
    techs = r.json()
    print(f"8. Technicians retrieved: {len(techs)} technicians.")

    # 9. Frontend HTML pages
    pages = [
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
    for p in pages:
        res = requests.get(f"{BASE}{p}")
        assert res.status_code == 200, f"Page {p} returned {res.status_code}"
    print(f"9. All {len(pages)} HTML pages, manifest, and service worker served successfully!")

    print("\n*** ALL LIVE END-TO-END VERIFICATION CHECKS PASSED 100% ***")

if __name__ == "__main__":
    run_checks()
