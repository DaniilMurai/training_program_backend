from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    email: EmailStr
    token: str | None = None