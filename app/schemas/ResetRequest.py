from pydantic import BaseModel, EmailStr


class ResetRequest(BaseModel):
    email: EmailStr
    code: str | None = None
