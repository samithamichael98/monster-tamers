
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

MONSTER_DB_PASSWORD = os.getenv("MONSTER_DB_PASSWORD")

if not MONSTER_DB_PASSWORD:
    raise RuntimeError("MONSTER_DB_PASSWORD is not configured")

DB_HOST = os.getenv("MONSTER_DB_HOST", "localhost")
DB_PORT = os.getenv("MONSTER_DB_PORT", "5434")

DATABASE_URL = (
    f"postgresql+psycopg://monster_service:"
    f"{quote_plus(MONSTER_DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/monster_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

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
