from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status

from app.db.models import User
from app.routes.users.router import hash_password


class AuthCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_user_by_email(self, email: EmailStr) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def update_user_password(self, email: EmailStr, new_password: str) -> dict[str, bool]:
        user = await self.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.password = hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        return {"success": True}
