from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

FILE_PATH = f"./campaigns.db"

SQL_ALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{FILE_PATH}"

engine = create_async_engine(
    SQL_ALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # Specific to SQLite, now we can use multiple threads for one db connection
)

# Creates a session every time we interact with backend db
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


# Generator to provide a db session each time the function is called
# Pauses execution and can be called again to resume
# Updated to async
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
