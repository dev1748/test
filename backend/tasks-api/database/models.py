from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import BigInteger, Column, String, ForeignKey, Table, func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from database.enums import TaskCategoryEnum

DB_USER = "testuser"
DB_PASSWORD = "passwd123"
DB_HOST = "postgres"
DB_PORT = 5432
DB_NAME = "mydb"

DATABASE_URL = (f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@"
                f"{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_async_engine(url=DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

class Task(Base):
    assigned_user_id: Mapped[Optional[int]]
    category: Mapped[TaskCategoryEnum]
    data_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    ai_pred: Mapped[Optional[str]]

    file_key_1: Mapped[Optional[str]]
    file_key_2: Mapped[Optional[str]]

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
