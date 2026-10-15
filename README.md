# Danfez Lift Management System
### Intelligent Elevator Fleet Monitoring, Simulation & Maintenance Platform (v2.0)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3.svg?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Capacitor](https://img.shields.io/badge/Capacitor-8.0-119EFF.svg?style=flat&logo=capacitor&logoColor=white)](https://capacitorjs.com/)
[![Android](https://img.shields.io/badge/Android_APK-Ready-3DDC84.svg?style=flat&logo=android&logoColor=white)](https://developer.android.com/)
[![License](https://img.shields.io/badge/License-Proprietary-07162B.svg?style=flat)]()

**Danfez Lift Management System** is a software project designed to simplify lift and elevator management through an organized and user-friendly interface. It aims to improve operational efficiency, streamline management tasks, and provide a reliable solution for handling lift-related operations.

Built for **DANFEZ TECH HOUSE**, the system features a responsive, mobile-first progressive architecture with an interactive virtual elevator simulator, real-time WebSocket telemetry, maintenance ticket dispatch workflows, automated fault triage, technician scheduling, analytics dashboards, and an installable native Android application packaged via Capacitor.

---

> [!IMPORTANT]
> **SAFETY & SIMULATION NOTICE:**
> This system operates as a **software-only simulation, monitoring, and facility dispatch environment**. It does **not** transmit actuation signals to physical elevator motors, safety brakes, door interlocks, or life-safety loop circuits. Physical elevator control must always remain under certified local hardware controllers and qualified elevator engineering personnel.

---

## 🌟 Key Features

### 1. 🛗 Interactive Elevator Simulator & Telemetry
- **Virtual Floor Motion:** Real-time physics simulator supporting floor-by-floor travel, realistic velocity curves, door dwell times, and multi-call dispatch queues.
- **Bi-directional WebSockets:** Sub-second telemetry feed synchronizes car position, status (`operational`, `moving`, `idle`, `maintenance`, `fault`), and door state (`open`, `closing`, `closed`) across all connected clients.
- **Interactive Controls:** Manual hall calls, cabin destination selection, door hold/open triggers, speed multiplier adjustments, and emergency stop testing.
- **Web Audio API Sound Engine:** Native dual-tone arrival chimes (D5/A4 chords) and mechanical warning alarms generated client-side without external audio file dependencies.

### 2. 📊 Executive Dashboard & Real-Time Analytics
- **Live Fleet KPIs:** Dynamic counts of total elevators, active operational units, lifts under maintenance, active safety alerts, and open work orders.
- **Safe Metric Calculation:** Zero-safe percentage computation and graceful offline/loading states preventing empty or broken UI metrics.
- **Visual Analytics:** Interactive Chart.js breakdown charts for fault severity (Critical, High, Medium, Low), maintenance ticket statuses, and 6-month fleet availability trends.
- **Live Audit Trail:** Chronological timeline tracking dispatcher commands, status updates, and elevator movements.

### 3. 🛠️ Maintenance & Work Order Management
- **Full Lifecycle Workflow:** Ticket creation, priority rating (`Critical`, `High`, `Medium`, `Low`), category classification (Mechanical, Electrical, Inspection, Sensor), and status tracking (`Open`, `Assigned`, `In Progress`, `Resolved`, `Closed`).
- **Technician Assignment:** Dispatch certified specialists according to workload, availability, and specific engineering expertise (Safety Brakes, Door Mechanisms, Drive Motors).
- **One-Click CSV Export:** Comprehensive report generation for maintenance records and incident logs.

### 4. 🚨 Safety & Fault Alert Center
- **Automated Fault Triage:** Immediate capture of overspeed warnings, door sensor obstructions, temperature spikes, and safety loop trips.
- **Triage Protocol:** Technician acknowledgement with timestamp logging, resolution notes, and automated ticket escalation.
- **Severity-based Filtering:** Filter by severity, acknowledgment status, resolution state, or elevator ID.

### 5. 🔐 Multi-User Authentication & Role-Based Access Control (RBAC)
- **Three Access Tiers:**
  - `Admin`: Full system control, building/lift creation, technician assignment, user management, and audit logs.
  - `Technician`: Work order management, fault resolution, and maintenance diagnostics.
  - `Viewer / Guest`: Live telemetry monitoring, floor observation, and operational summaries.
- **Enterprise Security:** Salted Bcrypt password hashing, signed PyJWT access tokens, server-side token revocation on logout (`jti` tracking), and single-use 60-minute password recovery tokens.
- **Google OAuth 2.0 Ready:** Native OpenID Connect workflow for corporate single sign-on.

### 6. 📱 Mobile-First Responsive Design & Standalone Android APK
- **Tested Mobile Viewports:** Precision-crafted for 360px, 390px, and 412px smartphone screens.
- **Touch-Friendly Controls:** Fixed bottom navigation bar with Android safe-area insets, responsive card layouts, and touch-scrolling data tables.
- **Native Android APK:** Packaged with Capacitor 8 and compiled with Java 17 / Android SDK 34+.
- **Signed Release APK:** Pre-signed with APK Signature Scheme v2 for direct sideloading without Google Play Store dependencies.

---

## 🏗️ Architecture & Technology Stack

```
Smart Lift Management System
├── backend/                  # FastAPI REST API & WebSocket Services
│   ├── app/
│   │   ├── auth/            # JWT authentication, security, and RBAC guards
│   │   ├── models/          # SQLAlchemy ORM models (Elevator, Building, Fault, Ticket, User)
│   │   ├── routers/         # API routes (elevators, simulator, faults, maintenance, reports)
│   │   ├── schemas/         # Pydantic v2 validation models
│   │   └── services/        # Real-time simulator engine & audit logger
│   └── database.py          # Database session factory & connection pooling
├── frontend/                 # Progressive Web App (HTML5, Bootstrap 5.3, JS, CSS)
│   ├── assets/              # Premium Navy/Electric Blue design system, icons, and audio
│   ├── dashboard.html       # Primary fleet KPI dashboard
│   ├── simulator.html       # Interactive 10-floor lift simulator
│   ├── lifts.html           # Elevator fleet inventory and configuration
│   ├── alerts.html          # Fault alerts and triage center
│   ├── maintenance.html     # Work orders and service tickets
│   ├── technicians.html     # Certified technician roster
│   └── reports.html         # Analytics charts and CSV export
├── android/                  # Native Android project (Capacitor 8.0)
│   ├── app/src/main/        # Android manifest, splash screens, mipmap icons
│   └── build.gradle         # Android build configurations (Java 17 target)
└── tests/                    # Automated Pytest test suite (38 test cases)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & **npm** (for Capacitor Android builds)
- **Android SDK & JDK 17** (optional, only for rebuilding the Android APK)

### 1. Clone the Repository
```bash
git clone https://github.com/danishalipny-pixel/Danfez-Lift-Management.git
cd Danfez-Lift-Management
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic pyjwt bcrypt python-multipart websockets pytest requests
```

### 3. Launch the Application
```bash
python run.py
```
The server will initialize the SQLite database (`danfez_lift.db`), populate initial demo seed data, and start on `http://localhost:8000`:
- **Web App:** [http://localhost:8000/dashboard.html](http://localhost:8000/dashboard.html)
- **Interactive API Docs (Swagger UI):** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Alternative ReDoc Docs:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

---

## 🧪 Automated Testing

The project includes a comprehensive automated test suite covering authentication, RBAC, elevator simulator dynamics, fault lifecycles, maintenance CRUD, and static routes.

Run the test suite with:
```bash
pytest -v
```
All **38 test cases** pass with 100% compliance:
```text
============================== 38 passed in 10.21s ==============================
```

---

## 📱 Android App Installation & Sideloading

The project comes with a pre-built, signed release APK ready for direct installation on any Android phone (Android 8.0+):

### File Location
- **Release APK:** [`Danfez-Lift-Management.apk`](./Danfez-Lift-Management.apk) (Root directory)

### Direct Installation Steps
1. Transfer `Danfez-Lift-Management.apk` to your Android device via USB Cable, WhatsApp, or Google Drive.
2. Tap the file in your phone's **Files** or **Downloads** app.
3. If prompted, enable **"Allow from this source"** for installation of unknown apps.
4. Tap **Install** and open **Danfez Lift Management**.

### Rebuilding the Android APK with Capacitor
To rebuild the APK from the latest web assets:
```powershell
# 1. Sync frontend web assets
npx cap sync android

# 2. Build release APK with Gradle
cd android
.\gradlew.bat assembleRelease

# 3. Copy APK to root
cd ..
Copy-Item "android\app\build\outputs\apk\release\app-release.apk" "Danfez-Lift-Management.apk" -Force
```

---

## 🔑 Demo Seed Accounts

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Chief Administrator** | `admin@danfez.com` | `Admin@12345` | Full system control, user management, settings |
| **Lead Technician** | `technician@danfez.com` | `Tech@12345` | Maintenance tasks, fault resolution, simulator |
| **Facility Viewer** | `viewer@danfez.com` | `Viewer@12345` | Read-only telemetry, floor observation |

---

## 🛡️ Security Best Practices

- **Zero Plaintext Credentials:** Passwords use salted bcrypt hashes with cost factor 12.
- **Signed JWT Tokens:** Cryptographically signed tokens with configurable expiration (8 hours default, 30 days for remember-me).
- **Session Revocation:** Revoked token JTI blacklisting on logout.
- **Android Network Security:** Cleartext HTTP restricted via `network_security_config.xml`.
- **Private Key Isolation:** Keystore and sensitive credentials excluded via `.gitignore`.

---

## 📄 License & Ownership

Developed by **DANFEZ TECH HOUSE**. All rights reserved.  
For inquiries, licensing, or commercial deployment, contact DANFEZ TECH HOUSE engineering team.
