import os

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Danfez Lift Control")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "danfez_tech_house_secure_jwt_dev_key_2026_xyz987")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")) # 8 hours
    REMEMBER_ME_EXPIRE_DAYS: int = int(os.getenv("REMEMBER_ME_EXPIRE_DAYS", "30")) # 30 days
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60")) # 1 hour
    
    # SQLite fallback for local development, PostgreSQL supported
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./danfez_lift.db")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    CORS_ORIGINS: list = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,*").split(",")
    ]
    
    # Email / SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@danfez.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "DANFEZ TECH HOUSE")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() in ("true", "1", "yes")
    
    # Google OAuth 2.0 / OpenID Connect
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Simulator Settings
    DEFAULT_FLOORS: int = int(os.getenv("DEFAULT_FLOORS", "10"))
    SIMULATOR_TICK_RATE_SECONDS: float = float(os.getenv("SIMULATOR_TICK_RATE_SECONDS", "1.0"))

settings = Settings()
