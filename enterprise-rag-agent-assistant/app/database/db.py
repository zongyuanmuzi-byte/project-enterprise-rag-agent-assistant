import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def ensure_sqlite_data_dir(database_url: str) -> None:
    """
    Ensure that the local data directory exists when using SQLite.

    Example:
    sqlite:///./data/app.db
    """
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")

        if db_path.startswith("./"):
            db_path = db_path[2:]

        directory = os.path.dirname(db_path)

        if directory:
            os.makedirs(directory, exist_ok=True)


ensure_sqlite_data_dir(settings.database_url)

connect_args = {}
engine_kwargs = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs = {"pool_pre_ping": True}


engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    Create and close a database session for each request.

    FastAPI will use this function as a dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all database tables.

    In a production-level project, Alembic is usually used for database migrations.
    In this beginner-friendly engineering foundation stage, automatic table creation is enough.
    """
    from app.database import models

    Base.metadata.create_all(bind=engine)
