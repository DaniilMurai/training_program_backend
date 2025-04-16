
from fastapi import HTTPException, status
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.UserModel import User
from app.schemas.UserSchema import UserSchema

from passlib.context import CryptContext


from fastapi import Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

from ..security.security import create_access_token, create_refresh_token, decode_token, token_blacklist
from ..database import get_async_db

# Настраиваем контекст хеширования (рекомендуется bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")