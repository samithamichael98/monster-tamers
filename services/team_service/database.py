import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

TEAM_DB_PASSWORD = os.getenv("TEAM_DB_PASSWORD")

if not TEAM_DB_PASSWORD:
    raise RuntimeError("TEAM_DB_PASSWORD is not configured")

DB_HOST = os.getenv("TEAM_DB_HOST", "localhost")
DB_PORT = os.getenv("TEAM_DB_PORT", "5435")

DATABASE_URL = (
    f"postgresql+psycopg://team_service:"
    f"{quote_plus(TEAM_DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/team_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()