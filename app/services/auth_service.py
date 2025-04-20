import random
from datetime import timedelta

import aiosmtplib
from fastapi import HTTPException
from pydantic import EmailStr

from app.crud.auth.read import AuthCRUD
from app.dependencies.redis import RedisClient
from app.schemas.ChangePasswordRequest import ChangePasswordRequest
from app.schemas.EmailRequest import EmailRequest
from app.schemas.ResetRequest import ResetRequest
from app.security.security import create_access_token
from app.services.email_service import EmailService


class AuthService:
    def __init__(
            self,
            redis: RedisClient,
            email_service: EmailService,
            auth_crud: AuthCRUD
    ):
        self.redis = redis
        self.email_service = email_service
        self.auth_crud = auth_crud



    async def send_reset_password(self, email: EmailStr):
        user = await self.auth_crud.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User with this email does not exist")
        token = create_access_token({"email":email}, timedelta(minutes=3))
        url = f"http://localhost:5173/reset-password-page/{token}"

        try:
            await self.email_service.send_email(email, "Сброс пароля", f'Перейдите по ссылке для сброса пароля:\n{url}')
            await self.redis.setex(f'reset:{email}', 180, token)

            return {"success": True}
        except aiosmtplib.SMTPAuthenticationError:
            raise HTTPException(status_code=500, detail="Ошибка аутентификации в SMTP")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке письма: {str(e)}")

    async def verify_reset_password(self, request: EmailRequest):
        email = request.email
        token = request.token

        stored_token = await self.redis.get(f'reset:{email}')

        if not stored_token:
            raise HTTPException(status_code=400, detail="Токен не найден или истёк")

        stored_token = stored_token.decode()

        if stored_token != token:
            raise HTTPException(status_code=400, detail="Неверный токен")

        return {"success": True}


    async def change_password(self, request: ChangePasswordRequest):

        db_user = await self.auth_crud.get_user_by_email(request.email)

        user = await self.auth_crud.update_user_password(db_user, request.new_password)
        await self.auth_crud.save_user_in_db(user)
        await self.redis.delete(f"reset:{request.email}")

        return {"success": True}


    async def send_reset_code(self, email: EmailStr):
        code = str(random.randint(100000, 999999))

        try:
            await self.email_service.send_email(email, "Confirmation code", f"Ваш код подтверждения: {code}")
            await self.redis.setex(f"reset:{email}", 180, code)
            return {"success": True}
        except aiosmtplib.SMTPAuthenticationError:
            raise HTTPException(status_code=500, detail="Ошибка аутентификации в SMTP")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке письма: {str(e)}")

    async def verify_reset_code(self, data: ResetRequest):
        email = data.email
        input_code = data.code

        stored_code = await self.redis.get(f"reset:{email}")

        if not stored_code:
            raise HTTPException(status_code=400, detail="Код не найден или истёк")

        stored_code = stored_code.decode()

        if stored_code != input_code:
            raise HTTPException(status_code=400, detail="Неверный код")

        return {"success": True}