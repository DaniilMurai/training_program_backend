from fastapi import APIRouter, Depends
from fastapi import Body
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import User
from app.db.session import get_async_db
from app.dependencies.dependencies import UserServiceDependency
from app.helpers.users.helpers import verify_password
from app.schemas.UserSchema import UserSchema, UserUpdateSchema
from app.schemas.oauth2_scheme import oauth2_scheme
from app.security.security import decode_token, create_access_token, create_refresh_token, token_blacklist
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

from app.schemas.TokenResponse import TokenResponse


@router.post("/check_if_user_not_exists")
async def check_if_user_exists(
        userdata: UserSchema,
        user_service: UserService = UserServiceDependency
):
    return await user_service.check_if_user_exists(userdata)


@router.get("", response_model=list[UserSchema])
async def get_users(
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        user_service: UserService = UserServiceDependency
):
    return await user_service.get_users(user_id, skip, limit)


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def post_user(
        userdata: UserSchema,
        user_service: UserService = UserServiceDependency
):
    return await user_service.post_user(userdata)


@router.patch("/{user_id}", response_model=UserSchema)
async def edit_user(
        user_id: int,
        userdata: UserUpdateSchema,
        user_service: UserService = UserServiceDependency
):
    return await user_service.edit_user(user_id, userdata)


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
        user_id: int,
        user_service: UserService = UserServiceDependency
):
    return await user_service.delete_user(user_id)


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(User).where(
            (User.email == form_data.username) | (User.name == form_data.username)  # type: ignore
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
        result = await db.execute(select(User).where(User.email == email))  # type: ignore
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
async def read_current_user(
        user_service: UserService = UserServiceDependency,
        token: str = Depends(oauth2_scheme),
):
    return await user_service.get_current_user(token)
