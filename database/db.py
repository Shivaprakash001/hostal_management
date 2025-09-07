import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable, fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/hostel.db")

# Handle SQLite vs PostgreSQL connection
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
else:
    # For PostgreSQL (Supabase/Neon)
    engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
Base = declarative_base()


def init_db() -> None:
    import models.models
    import models.upi_settings
    # Create tables if they don't exist (idempotent operation)
    Base.metadata.create_all(bind=engine)

def get_db():
    db =Session()
    try:
        yield db
    finally:
        db.close()
