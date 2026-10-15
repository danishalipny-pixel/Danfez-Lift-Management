from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# Engine setup
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Create all tables and perform lightweight SQLite schema migrations if needed."""
    Base.metadata.create_all(bind=engine)
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(users)"))
                cols = {row[1] for row in res.fetchall()}
                if cols:
                    if "is_verified" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 1"))
                    if "verification_token" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)"))
                    if "verification_token_expires" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires DATETIME"))
                    if "google_id" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
                    if "avatar_url" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                    conn.commit()
            except Exception as e:
                print(f"[DB] Migration check notice: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
