from passlib.context import CryptContext

# Настраиваем контекст хеширования (рекомендуется bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Хелпер-функции (синхронные, но быстрые)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)