from fastapi import Depends, HTTPException
from jose import JWTError
from starlette import status

from app.crud.auth.read import AuthCRUD
from app.schemas.UserSchema import UserSchema, UserUpdateSchema
from app.schemas.oauth2_scheme import oauth2_scheme
from app.security.security import decode_token, create_access_token, create_refresh_token


class UserService:
    def __init__(
            self,
            auth_crud: AuthCRUD
    ):
        self.auth_crud = auth_crud

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
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

            user = await self.auth_crud.get_user_by_email(email)

            if not user:
                raise credentials_exception
            return user
        except JWTError as e:
            print(f"JWT Error: {e}")
            raise credentials_exception

    async def check_if_user_exists(self, userdata: UserSchema):
        email_exists = await self.auth_crud.get_user_by_email(userdata.email)
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "email",
                    "message": "Email already registered",
                    "field": "email"
                }
            )
        name_exists = await self.auth_crud.get_user_by_name(userdata.name)
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "username",
                    "message": "Username already taken",
                    "field": "name"
                }
            )
        return {"success": True}

    async def get_users(
            self,
            user_id: int | None = None,
            skip: int = 0,
            limit: int = 100
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
            user = await self.auth_crud.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found"
                )
            return [user]

        return await self.auth_crud.get_users(skip, limit)

    async def post_user(
            self,
            userdata: UserSchema,
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

        await self.check_if_user_exists(userdata)

        new_user = await self.auth_crud.create_user(userdata)

        return {
            "access_token": create_access_token(
                data={"sub": new_user.email, "type": "access"}
            ),
            "refresh_token": create_refresh_token(
                data={"sub": new_user.email, "type": "refresh"}
            ),
            "token_type": "bearer",
        }

    async def edit_user(
            self,
            user_id: int,
            userdata: UserUpdateSchema
    ):
        if not any([userdata.name, userdata.email, userdata.password]):
            raise HTTPException(status_code=400, detail="No fields to update provided")

        async with self.auth_crud.db.begin():
            db_user = await self.auth_crud.get_user_by_id(user_id)

            fields_to_update = {}

            if userdata.name is not None:
                fields_to_update["name"] = userdata.name
            if userdata.email is not None:
                fields_to_update["email"] = userdata.email

            if fields_to_update:
                db_user = await self.auth_crud.update_user_fields(db_user, **fields_to_update)

            if userdata.password is not None:
                db_user = await self.auth_crud.update_user_password(db_user, userdata.password)

        # здесь транзакция уже закоммичена
        await self.auth_crud.db.refresh(db_user)

        return db_user

    async def delete_user(
            self,
            user_id: int
    ):
        user = await self.auth_crud.get_user_by_id(user_id)
        return await self.auth_crud.delete_user(user)
