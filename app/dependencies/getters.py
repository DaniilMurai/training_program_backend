from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.auth.read import AuthCRUD
from app.db.session import get_async_db
from app.dependencies.redis import RedisClient
from app.services.auth_service import AuthService
from app.services.email_service import EmailService


async def get_email_service() -> EmailService:
    return EmailService()


async def get_redis_client() -> RedisClient:
    return RedisClient()



async def get_auth_service(
    redis: RedisClient = Depends(get_redis_client),
    email_service: EmailService = Depends(get_email_service),
    db: AsyncSession = Depends(get_async_db)
) -> AuthService:
    auth_crud = AuthCRUD(db)
    return AuthService(redis, email_service, auth_crud)