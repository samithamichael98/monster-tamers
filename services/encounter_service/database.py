
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

ENCOUNTER_DB_PASSWORD = os.getenv("ENCOUNTER_DB_PASSWORD")

if not ENCOUNTER_DB_PASSWORD:
    raise RuntimeError("ENCOUNTER_DB_PASSWORD is not configured")

DB_HOST = os.getenv("ENCOUNTER_DB_HOST", "localhost")
DB_PORT = os.getenv("ENCOUNTER_DB_PORT", "5436")

DATABASE_URL = (
    f"postgresql+psycopg://encounter_service:"
    f"{quote_plus(ENCOUNTER_DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/encounter_db"
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
