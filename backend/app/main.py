import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .config import settings
from .database import engine, Base, SessionLocal, init_db
from .services.seed_data import seed_database
from .services.simulator_engine import simulator_manager
from .models.elevator import Elevator

# Import routers
from .routers import (
    auth_router,
    users_router,
    buildings_router,
    elevators_router,
    simulator_router,
    maintenance_router,
    faults_router,
    technicians_router,
    reports_router,
    settings_router,
    health_router
)

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    print("[DANFEZ] Initializing DANFEZ TECH HOUSE - Smart Lift Management System...")
    # 1. Create DB tables & ensure schema
    init_db()
    
    # 2. Seed initial demonstration data
    db = SessionLocal()
    try:
        seed_database(db)
        # 3. Preload all elevators into simulator manager
        elevators = db.query(Elevator).all()
        for e in elevators:
            simulator_manager.get_or_create(e.id, e.floor_count, e.current_floor)
        print(f"[DANFEZ] Loaded {len(elevators)} elevators into simulator engine.")
    finally:
        db.close()

    # 4. Start background simulator tick loop
    simulator_manager.start()
    print("[DANFEZ] Elevator simulation background engine active.")

    yield

    # Shutdown:
    print("[DANFEZ] Shutting down simulator engine...")
    simulator_manager.stop()

app = FastAPI(
    title="Danfez Lift Control API",
    description="Intelligent Elevator Monitoring & Maintenance Backend API for DANFEZ TECH HOUSE",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permissive for local development & PWA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error in request payload", "errors": exc.errors()},
    )

# Include API Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(buildings_router)
app.include_router(elevators_router)
app.include_router(simulator_router)
app.include_router(maintenance_router)
app.include_router(faults_router)
app.include_router(technicians_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(health_router)

# Mount static assets if directory exists
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Serve PWA manifest and service worker from frontend root
@app.get("/manifest.json")
async def get_manifest():
    manifest_path = FRONTEND_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")
    return JSONResponse(status_code=404, content={"detail": "Manifest not found"})

@app.get("/service-worker.js")
async def get_service_worker():
    sw_path = FRONTEND_DIR / "service-worker.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript")
    return JSONResponse(status_code=404, content={"detail": "Service worker not found"})

# Serve frontend HTML files directly for easy SPA / multi-page navigation
PAGES = [
    "index.html",
    "login.html",
    "register.html",
    "forgot-password.html",
    "reset-password.html",
    "verify-email.html",
    "dashboard.html",
    "lifts.html",
    "simulator.html",
    "maintenance.html",
    "alerts.html",
    "technicians.html",
    "reports.html",
    "users.html",
    "settings.html",
    "profile.html",
    "offline.html"
]

for page in PAGES:
    def make_handler(p):
        async def page_handler():
            target_path = FRONTEND_DIR / p
            if target_path.exists():
                return FileResponse(str(target_path), media_type="text/html")
            return JSONResponse(status_code=404, content={"detail": f"{p} not found"})
        return page_handler

    app.add_api_route(f"/{page}", make_handler(page), methods=["GET"])

@app.get("/")
async def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    return RedirectResponse(url="/dashboard.html")
