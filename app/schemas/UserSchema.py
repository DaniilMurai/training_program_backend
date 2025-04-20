from typing import Optional

from pydantic import EmailStr, BaseModel, Field


class UserSchema(BaseModel):
    id: int | None = None
    name: str
    email: EmailStr
    password: str | None = None


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None, min_length=8)
