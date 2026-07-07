from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///friend_cal.db")

engine = create_async_engine(DATABASE_URL, echo=False)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
