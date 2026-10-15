from .auth import router as auth_router
from .users import router as users_router
from .buildings import router as buildings_router
from .elevators import router as elevators_router
from .simulator import router as simulator_router
from .maintenance import router as maintenance_router
from .faults import router as faults_router
from .technicians import router as technicians_router
from .reports import router as reports_router
from .settings import router as settings_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "users_router",
    "buildings_router",
    "elevators_router",
    "simulator_router",
    "maintenance_router",
    "faults_router",
    "technicians_router",
    "reports_router",
    "settings_router",
    "health_router"
]
