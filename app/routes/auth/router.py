import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from app.dependencies.dependencies import AuthServiceDependency
from app.routes.auth.helpers import help_validate_token
from app.routes.users.router import oauth2_scheme
from app.schemas.ChangePasswordRequest import ChangePasswordRequest
from app.schemas.Email import Email
from app.schemas.EmailRequest import EmailRequest
from app.schemas.ResetRequest import ResetRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=["auth"])

load_dotenv()

# Создание подключения к Redis
redis_client = redis.from_url("redis://localhost:6379")


@router.get("/validate")
async def validate_token(token: str = Depends(oauth2_scheme)):
    return await help_validate_token(token)


@router.post("/send-reset-password")
async def send_reset_password(
        email: Email,
        auth_service: AuthService = AuthServiceDependency
):
    return await auth_service.send_reset_password(email.email)


@router.post("/verify-reset-password")
async def verify_reset_password(
        request: EmailRequest,
        auth_service: AuthService = AuthServiceDependency
):
    return await auth_service.verify_reset_password(request)


@router.patch("/change-password")
async def change_password(
        request: ChangePasswordRequest,
        auth_service: AuthService = AuthServiceDependency
):
    return await auth_service.change_password(request)


@router.post("/send-confirmation-code")
async def send_confirmation_code(
        email: Email,
        auth_service: AuthService = AuthServiceDependency
):
    return await auth_service.send_reset_code(email.email)


@router.post("/verify-reset-code")
async def verify_confirmation_code(
        data: ResetRequest,
        auth_service: AuthService = AuthServiceDependency
):
    return await auth_service.verify_reset_code(data)
