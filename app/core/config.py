from pydantic import Field, EmailStr  # Остальные импорты из pydantic
from pydantic_settings import BaseSettings  # Новый импорт


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(default="secret", env="SECRET_KEY")
    # Добавляем email-переменные
    EMAIL_USER: EmailStr = Field(..., env="EMAIL_USER")
    EMAIL_PASSWORD: str = Field(..., env="EMAIL_PASSWORD")
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    BASE_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"  # Загрузка переменных из файла


settings = Settings()