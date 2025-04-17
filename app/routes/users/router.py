from app.db.models import User
from app.db.session import get_async_db
from app.security.security import decode_token, create_access_token, create_refresh_token, token_blacklist

from fastapi import HTTPException, status
from fastapi import APIRouter, Depends


from app.schemas.UserSchema import UserSchema

from passlib.context import CryptContext


from fastapi import Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

router = APIRouter(prefix="/users", tags=["users"])

# Настраиваем контекст хеширования (рекомендуется bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.schemas.TokenResponse import TokenResponse

# Инициализация
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")



# Хелпер-функции (синхронные, но быстрые)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Асинхронные зависимости
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if not token:
            raise credentials_exception

        payload = decode_token(token)
        if payload.get("type") != "access" or not payload.get("sub"):
            raise credentials_exception

        email = payload.get("sub")
        result = await db.execute(select(User).where(User.email == email)) # type: ignore
        user = result.scalars().first()

        if not user:
            raise credentials_exception

        return user

    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception


@router.post("/check_if_user_not_exists")
async def check_if_user_exists(userdata: UserSchema, db: AsyncSession = Depends(get_async_db)):
    # Проверка существующего пользователя
    email_exists = await db.execute(select(User).where(User.email == userdata.email))
    if email_exists.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "email",
                "message": "Email already registered",
                "field": "email"
            }
        )
    name_exists = await db.execute(select(User).where(User.name == userdata.name))
    if name_exists.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "username",
                "message": "Username already taken",
                "field": "name"
            }
        )

    return {"success": True}


# Роуты
@router.get("", response_model=list[UserSchema])
async def get_users(
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_async_db)
):
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be bigger than 0"
        )
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip must be equal or bigger than 0"
        )

    if user_id:
        result = await db.execute(select(User).where(User.id == user_id)) # type: ignore
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        return [user]

    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def post_user(
        userdata: UserSchema,
        db: AsyncSession = Depends(get_async_db)
):

    if len(userdata.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "password",
                "message": "Password must be at least 8 characters",
                "field": "password"
            }
        )




    #Проверка существующего пользователя
    email_exists = await db.execute(select(User).where(User.email == userdata.email))
    if email_exists.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "email",
                "message": "Email already registered",
                "field": "email"
            }
        )
    name_exists = await db.execute(select(User).where(User.name == userdata.name))
    if name_exists.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "username",
                "message": "Username already taken",
                "field": "name"
            }
        )


    # Создание нового пользователя
    new_user = User(
        name=userdata.name,
        email=userdata.email,
        password=hash_password(userdata.password)
    )


    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "access_token": create_access_token(
            data={"sub": new_user.email, "type": "access"}
        ),
        "refresh_token": create_refresh_token(
            data={"sub": new_user.email, "type": "refresh"}
        ),
        "token_type": "bearer",
    }


@router.patch("/{user_id}", response_model=UserSchema)
async def edit_user(
        user_id: int,
        userdata: UserSchema,
        db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(User).where(User.id == user_id)) # type: ignore
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Обновление имени
    if userdata.name is not None:
        if userdata.name != db_user.name:
            name_result = await db.execute(
                select(User).where(
                    (User.name == userdata.name) & (User.id != user_id) # type: ignore
                ) # type: ignore
            ) # type: ignore
            if name_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Name already registered by another user"
                )
            db_user.name = userdata.name

    # Обновление email
    if userdata.email is not None:
        if userdata.email != db_user.email:
            email_result = await db.execute(
                select(User).where(
                    (User.email == userdata.email) & (User.id != user_id) # type: ignore
                )
            )
            if email_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered by another user"
                )
            db_user.email = userdata.email

    # Обновление пароля
    if userdata.password is not None:
        db_user.password = hash_password(userdata.password)

    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(User).where(User.id == user_id)) # type: ignore
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return user


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(User).where(
            (User.email == form_data.username) | (User.name == form_data.username) # type: ignore
        )
    )
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "Invalid credentials",
                "message": "Wrong login or password",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(data={"sub": user.email, "type": "access"}),
        "refresh_token": create_refresh_token(data={"sub": user.email, "type": "refresh"}),
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_the_token(
        refresh_token: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_db)
):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")

        email = payload.get("sub")
        result = await db.execute(select(User).where(User.email == email)) # type: ignore
        user = result.scalars().first()

        if not user:
            raise JWTError("User not found")

        return {
            "access_token": create_access_token(data={"sub": email}),
            "refresh_token": create_refresh_token(data={"sub": user.email})
        }

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout")
async def logout(refresh_token: str = Body(..., embed=True)):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        token_blacklist.add(refresh_token)
        return {"message": "Successfully logged out"}

    except JWTError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserSchema)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user