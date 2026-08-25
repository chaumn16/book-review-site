import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.sqlite")
# Some Postgres providers (Render, old Heroku-style URLs) hand out
# "postgres://" -- SQLAlchemy 1.4+ requires the "postgresql://" scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args = {}
_engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    if DATABASE_URL == "sqlite:///:memory:":
        # Share the single in-memory DB across connections (needed for tests).
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
