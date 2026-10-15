from .auth import (
    LoginRequest, RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest,
    VerifyEmailRequest, GoogleAuthRequest, ProfileUpdateRequest,
    Token, TokenData, PasswordChangeRequest
)
from .user import UserBase, UserCreate, UserUpdate, UserResponse
from .building import BuildingBase, BuildingCreate, BuildingResponse
from .elevator import (
    ElevatorBase, ElevatorCreate, ElevatorUpdate, ElevatorResponse,
    SimulatorCallRequest, SimulatorDoorRequest, SimulatorSpeedRequest, SimulatorTestFaultRequest
)
from .technician import TechnicianBase, TechnicianCreate, TechnicianUpdate, TechnicianResponse
from .maintenance import MaintenanceTicketBase, MaintenanceTicketCreate, MaintenanceTicketUpdate, MaintenanceTicketResponse
from .fault import FaultAlertBase, FaultAlertCreate, FaultAlertAcknowledge, FaultAlertResolve, FaultAlertResponse
from .audit import AuditLogResponse
from .setting import SettingUpdate, SettingResponse, SystemConfigUpdate

__all__ = [
    "LoginRequest", "RegisterRequest", "ForgotPasswordRequest", "ResetPasswordRequest",
    "VerifyEmailRequest", "GoogleAuthRequest", "ProfileUpdateRequest",
    "Token", "TokenData", "PasswordChangeRequest",
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "BuildingBase", "BuildingCreate", "BuildingResponse",
    "ElevatorBase", "ElevatorCreate", "ElevatorUpdate", "ElevatorResponse",
    "SimulatorCallRequest", "SimulatorDoorRequest", "SimulatorSpeedRequest", "SimulatorTestFaultRequest",
    "TechnicianBase", "TechnicianCreate", "TechnicianUpdate", "TechnicianResponse",
    "MaintenanceTicketBase", "MaintenanceTicketCreate", "MaintenanceTicketUpdate", "MaintenanceTicketResponse",
    "FaultAlertBase", "FaultAlertCreate", "FaultAlertAcknowledge", "FaultAlertResolve", "FaultAlertResponse",
    "AuditLogResponse",
    "SettingUpdate", "SettingResponse", "SystemConfigUpdate"
]
