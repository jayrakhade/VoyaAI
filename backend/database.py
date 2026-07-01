"""
database.py

SQLAlchemy database setup and session management.

Architecture:
- Engine: Connection to PostgreSQL
- SessionLocal: Factory for creating sessions
- get_db: Dependency for getting database session
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from models.conversation import Base

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/voyaai"
)


def _ensure_database_exists(db_url: str) -> None:
    """
    Create the target database if it does not already exist.

    Connects to the default 'postgres' maintenance database first,
    then issues CREATE DATABASE if needed. This runs once at startup
    so the app never crashes with 'database does not exist'.

    Args:
        db_url: Full DATABASE_URL (e.g. postgresql://user:pass@host:5432/voyaai)
    """
    # Parse out the database name and build a URL pointing to 'postgres' db
    # e.g. postgresql://postgres:pass@localhost:5432/voyaai
    #   →  postgresql://postgres:pass@localhost:5432/postgres
    if "/" not in db_url.rsplit(":", 1)[-1]:
        return  # Cannot parse — skip

    base_url, db_name = db_url.rsplit("/", 1)
    # Strip query params from db_name if present
    db_name = db_name.split("?")[0]
    maintenance_url = f"{base_url}/postgres"

    try:
        # isolation_level=AUTOCOMMIT required — CREATE DATABASE cannot run
        # inside a transaction block
        maintenance_engine = create_engine(
            maintenance_url,
            isolation_level="AUTOCOMMIT",
        )
        with maintenance_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).fetchone()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"[database] Created database '{db_name}'")
            else:
                print(f"[database] Database '{db_name}' already exists")
        maintenance_engine.dispose()
    except Exception as e:
        print(f"[database] Could not auto-create database: {e}")
        raise


# Auto-create the database before building the engine
_ensure_database_exists(DATABASE_URL)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Create all tables defined in the ORM models.

    Safe to call on every startup — SQLAlchemy uses CREATE TABLE IF NOT EXISTS
    so existing tables and data are never touched.
    """
    Base.metadata.create_all(bind=engine)
    print("[database] All tables ready")



# Context manager for database sessions.
# IMPORTANT: Does NOT auto-commit on exit.
# All commits must be explicit inside the with-block.
# This prevents double-commit bugs when service methods commit internally.
class DBSession:
    """Context manager for database sessions — explicit commit only."""

    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        self.db.close()
