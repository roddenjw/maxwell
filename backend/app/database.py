"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

# Get database path from environment or use default
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR}/codex.db"
)

# Create engine
# For SQLite, we use check_same_thread=False to allow multi-threading
# StaticPool is used for in-memory databases during testing
# Connection pooling settings to prevent resource exhaustion
if DATABASE_URL.startswith("sqlite"):
    if ":memory:" in DATABASE_URL:
        # In-memory database uses StaticPool
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
    else:
        # File-based SQLite with connection limits
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            pool_size=5,  # Max 5 persistent connections
            max_overflow=10,  # Max 10 additional connections when needed
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )
else:
    # PostgreSQL/MySQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database sessions
    Usage in FastAPI routes:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Call this on application startup
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all tables - use with caution!
    Only for development/testing
    """
    Base.metadata.drop_all(bind=engine)
