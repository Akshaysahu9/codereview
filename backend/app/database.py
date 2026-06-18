import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _sqlite_url() -> str:
    if os.getenv("RENDER"):
        return "sqlite:////tmp/codereview.db"
    return "sqlite:///./codereview.db"


def _resolve_database_url() -> str:
    url = settings.database_url.strip()
    if url.startswith("postgres"):
        # Linked Render Postgres sets DATABASE_URL but this app uses SQLite only.
        return _sqlite_url()
    if url.startswith("sqlite"):
        return url
    return _sqlite_url()


_db_url = _resolve_database_url()
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
