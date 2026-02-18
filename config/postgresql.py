# File: `config/postgresql.py`
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

# Load .env file if present
load_dotenv()

DB_HOST = os.getenv("POSTGRES_SERVER") or os.getenv("DB_HOST")
DB_PORT = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT")
DB_NAME = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME")
DB_USER = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")

if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB_NAME, DB_USER and DB_PASSWORD environment variables must be set")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


# Async database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_postgres_connection():
    """
    Yields a live psycopg2 connection and ensures it is closed after use.
    Uses the `DB_*` variables loaded above (from POSTGRES_* or DB_* envs).
    """
    conn = None
    try:
        host = DB_HOST or "localhost"
        port = int(DB_PORT) if DB_PORT else 5432
        dbname = DB_NAME
        user = DB_USER
        password = DB_PASSWORD

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        yield conn
    finally:
        if conn:
            conn.close()
