import os

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_async_engine(DATABASE_URL,
                             echo=True,  # Логгирование SQL-запросов (для разработки)
                             future=True,  # Для SQLAlchemy 2.0+
                             )
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)




async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session