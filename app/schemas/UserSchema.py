from pydantic import EmailStr, BaseModel


class UserSchema(BaseModel):
    id: int | None = None
    name: str
    email: EmailStr
    password: str | None = None

