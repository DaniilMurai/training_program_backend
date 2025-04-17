from fastapi import FastAPI

from app.routes import users, auth, health

router = FastAPI()


router.include_router(users.router)
router.include_router(auth.router)
router.include_router(health.router)

