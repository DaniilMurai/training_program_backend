from fastapi import Depends, HTTPException
from jose import JWTError

from app.routes.users.router import oauth2_scheme
from app.security.security import decode_token


async def help_validate_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        return {"valid": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
