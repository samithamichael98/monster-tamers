
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

USER_DB_PASSWORD = os.getenv("USER_DB_PASSWORD")

if not USER_DB_PASSWORD:
    raise RuntimeError("USER_DB_PASSWORD is not configured")

DB_HOST = os.getenv("USER_DB_HOST", "localhost")
DB_PORT = os.getenv("USER_DB_PORT", "5433")

DATABASE_URL = (
    f"postgresql+psycopg://user_service:"
    f"{quote_plus(USER_DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/user_db"
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
