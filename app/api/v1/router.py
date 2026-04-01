from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users

router = APIRouter()


@router.get("/ping", tags=["Utils"])
async def ping():
    return {"message": "pong"}


router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
