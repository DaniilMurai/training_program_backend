from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.testing import future

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:1111@localhost:5432/fastapi_db"


engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                             echo=True,  # Логгирование SQL-запросов (для разработки)
                             future=True,  # Для SQLAlchemy 2.0+
                             )
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)




async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session