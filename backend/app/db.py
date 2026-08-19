import logging
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

logger = logging.getLogger("shipguard.db")
settings = get_settings()

db_url = os.environ.get("DATABASE_URL") or settings.database_url
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,  # Test connections for liveness before using from pool
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if db_url == "sqlite:///shipguard.db" and not os.path.exists("shipguard.db") and os.path.exists("backend/shipguard.db"):
        db_url = "sqlite:///backend/shipguard.db"
else:
    # Production connection pool parameters for Oracle / PostgreSQL
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,  # Recycle connections every 30 minutes
        "pool_timeout": 30,
    })

engine = create_engine(db_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
