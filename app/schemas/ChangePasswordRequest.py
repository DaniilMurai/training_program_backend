from pydantic import BaseModel, EmailStr


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str