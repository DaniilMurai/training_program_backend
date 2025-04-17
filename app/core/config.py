from pydantic_settings import BaseSettings  # Новый импорт
from pydantic import Field, EmailStr  # Остальные импорты из pydantic


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(default="secret", env="SECRET_KEY")
    # Добавляем email-переменные
    EMAIL_USER: EmailStr = Field(..., env="EMAIL_USER")
    EMAIL_PASSWORD: str = Field(..., env="EMAIL_PASSWORD")

    class Config:
        env_file = ".env"  # Загрузка переменных из файла


settings = Settings()