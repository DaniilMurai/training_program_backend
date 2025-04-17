
import os
import random
from datetime import timedelta
from email.message import EmailMessage

import aiosmtplib
from dotenv import load_dotenv


from app.routes.users.router import oauth2_scheme, hash_password
from app.schemas.ChangePasswordRequest import ChangePasswordRequest
from app.schemas.EmailRequest import EmailRequest
from app.schemas.ResetRequest import ResetRequest

import redis.asyncio as redis

from app.db.models import User
from app.db.session import get_async_db
from app.security.security import decode_token, create_access_token

from fastapi import HTTPException, status
from fastapi import APIRouter, Depends


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

router = APIRouter(prefix='/auth', tags=["auth"])


load_dotenv()

# Создание подключения к Redis
redis_client = redis.from_url("redis://localhost:6379")



@router.get("/validate")
async def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        return {"valid": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



@router.post("/send-reset-password")
async def send_reset_password(
        request: EmailRequest,
        db: AsyncSession = Depends(get_async_db)  # Используем Depends()
):
    result = await db.execute(select(User).where(User.email == request.email))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")

    email = request.email
    message = EmailMessage()

    email_dict = {"email": email}
    token = create_access_token(email_dict, timedelta(minutes=3))
    url = f"http://localhost:5173/reset-password-page/{token}"

    message["FROM"] = os.getenv("EMAIL_USER")
    message["TO"] = email
    message["Subject"] = "Сброс пароля"
    message.set_content(f'Перейдите по ссылке для сброса пароля:\n{url}')

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=os.getenv("EMAIL_USER"),
            password=os.getenv("EMAIL_PASSWORD")
        )
        await redis_client.setex(f'reset:{email}', 180, token)
        return {"success": True}

    except aiosmtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="Ошибка аутентификации в SMTP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке письма: {str(e)}")

@router.post("/verify-reset-password")
async def verify_reset_password(request: EmailRequest):
    email = request.email
    token = request.token

    stored_token = await redis_client.get(f'reset:{email}')

    if not stored_token:
        raise HTTPException(status_code=400, detail="Токен не найден или истёк")

    stored_token = stored_token.decode()

    if stored_token != token:
        raise HTTPException(status_code=400, detail="Неверный токен")

    return {"success": True}

@router.patch("/change-password")
async def change_password(request: ChangePasswordRequest, db: AsyncSession = Depends(get_async_db)):


    result = await db.execute(select(User).where(User.email == request.email))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


    db_user.password = hash_password(request.new_password)

    await db.commit()
    await db.refresh(db_user)

    await redis_client.delete(f"reset:{request.email}")

    return {"success": True}


@router.post("/send-confirmation-code")
async def send_reset_code(data: ResetRequest):

    print(data)
    print(os.getenv("EMAIL_USER"))
    print(os.getenv("EMAIL_PASSWORD"))
    code = str(random.randint(100000, 999999))
    email = data.email



    message = EmailMessage()

    message["FROM"] = os.getenv("EMAIL_USER")
    message["TO"] = email
    message["Subject"] = "Confirmation code"
    message.set_content(f"Ваш код подтверждения: {code}")

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=os.getenv("EMAIL_USER"),
            password=os.getenv("EMAIL_PASSWORD")
        )

        # Сохранение кода в Redis с TTL 5 минут
        await redis_client.setex(f"reset:{email}", 180, code)  # 180 секунд = 3 минуты
        print(f"Отправлен код {code} для {email}")
        #сохрангить код в базе для последующей проверки
        return {"success": True}
    except aiosmtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="Ошибка аутентификации в SMTP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке письма: {str(e)}")


@router.post("/verify-reset-code")
async def verify_reset_code(data: ResetRequest):
    email = data.email
    input_code = data.code

    stored_code = await redis_client.get(f"reset:{email}")

    if not stored_code:
        raise HTTPException(status_code=400, detail="Код не найден или истёк")

    stored_code = stored_code.decode()

    if stored_code != input_code:
        raise HTTPException(status_code=400, detail="Неверный код")

    return {"success": True}

