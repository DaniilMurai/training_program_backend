from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status

from app.db.models import User
from app.helpers.users.helpers import hash_password
from app.schemas.UserSchema import UserSchema


class AuthCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_unique_fields(self, exclude_user_id: int = None, **kwargs):
        query = select(User)

        # Добавляем все условия поля=значение
        for field, value in kwargs.items():
            query = query.where(getattr(User, field) == value)

        # Исключаем пользователя, если нужно
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)

        result = await self.db.execute(query)
        if result.scalars().first():
            fields_str = ', '.join(f"{key}='{value}'" for key, value in kwargs.items())
            raise HTTPException(status_code=409, detail=f"User with {fields_str} already exists")

    async def get_users(self, skip: int, limit: int):
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_by_email(self, email: EmailStr) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_name(self, name: str):
        result = await self.db.execute(select(User).where(User.name == name))
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int):
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def update_user_fields(self, user: User, **fields_to_update):
        # Проверяем: не обновляем ли мы поля на те же самые значения
        same_fields = [
            field for field, value in fields_to_update.items()
            if getattr(user, field) == value
        ]
        if same_fields:
            fields_str = ', '.join(same_fields)
            raise HTTPException(status_code=409, detail=f"New values for {fields_str} match the current ones")

        # Проверка на уникальность
        await self._check_unique_fields(exclude_user_id=user.id, **fields_to_update)

        # Обновляем поля
        for field, value in fields_to_update.items():
            setattr(user, field, value)
        
        return user

    async def update_user_name(self, db_user: User, name: str) -> User:

        if name != db_user.name:
            name_result = await self.db.execute(
                select(User).where(
                    (User.name == name) & (User.id != db_user.id)
                )
            )
            if name_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Name already registered by another user"
                )
            db_user.name = name

            return db_user
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Your name already set to {db_user.name}"
        )

    async def update_user_email(self, db_user: User, email: EmailStr) -> User:
        if email != db_user.email:
            email_result = await self.db.execute(
                select(User).where(
                    (User.email == email) & (User.id != db_user.id)  # type: ignore
                )
            )
            if email_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered by another user"
                )
            db_user.email = email

            return db_user
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Your email already set to {db_user.email}"
        )

    async def update_user_password(self, db_user: User, new_password: str) -> User:
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if new_password != db_user.password:
            db_user.password = hash_password(new_password)
            return db_user

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You can't change the password to the one you have"
        )

    async def save_user_in_db(self, user: User) -> User:
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Data conflict occurred: {e}"
            )

    async def create_user(self, userdata: UserSchema) -> UserSchema:
        try:
            new_user = User(
                name=userdata.name,
                email=userdata.email,
                password=hash_password(userdata.password)
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)

            return new_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {e}"
            )

    async def delete_user(self, user: User) -> User:

        await self.db.delete(user)

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

        return user
