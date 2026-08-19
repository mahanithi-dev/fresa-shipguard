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

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # If running from project root and backend/shipguard.db exists
    if db_url == "sqlite:///shipguard.db" and not os.path.exists("shipguard.db") and os.path.exists("backend/shipguard.db"):
        db_url = "sqlite:///backend/shipguard.db"

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
