from pydantic import EmailStr, field_validator

from . import BaseModel

class UserSchema(BaseModel):
    id: int | None = None
    name: str
    email: EmailStr
    password: str | None = None

