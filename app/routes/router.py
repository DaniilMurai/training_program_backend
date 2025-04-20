from fastapi import APIRouter

from app.routes import users, auth, health

router = APIRouter()

router.include_router(users.router)
router.include_router(auth.router)
router.include_router(health.router)
