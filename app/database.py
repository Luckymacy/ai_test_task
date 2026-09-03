import os
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


parts = urlsplit(DATABASE_URL)

ASYNC_DATABASE_URL = urlunsplit(
    (
        "postgresql+asyncpg",
        parts.netloc,
        parts.path,
        "",
        "",
    )
)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    connect_args={"ssl": "require"},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)