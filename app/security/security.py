from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional


SECRET_KEY = "zPcKL4Nw5"
ALGORITHM = "HS256"  # Алгоритм подписи
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Время жизни токена
REFRESH_TOKEN_EXPIRE_DAYS = 7


token_blacklist = set()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT-токен на основе переданных данных."""
    to_encode = data.copy()

    # Устанавливаем срок действия токена
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает Refresh Token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    """Декодирует JWT и проверяет, не в черном списке ли он."""
    if token in token_blacklist:
        raise JWTError("Token revoked")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}")
