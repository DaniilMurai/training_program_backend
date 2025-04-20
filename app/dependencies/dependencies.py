from fastapi import Depends

from app.db.session import get_async_db
from app.dependencies.getters import get_email_service, get_auth_service, get_user_service

DatabaseDependency = Depends(get_async_db)
EmailServiceDependency = Depends(get_email_service)
AuthServiceDependency = Depends(get_auth_service)
UserServiceDependency = Depends(get_user_service)
