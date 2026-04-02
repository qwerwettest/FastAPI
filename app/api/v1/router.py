from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import ip_claims
from app.api.v1.endpoints import patents
from app.api.v1.endpoints import users

router = APIRouter()


@router.get("/ping", tags=["Utils"])
async def ping():
    return {"message": "pong"}


router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# Legacy CRUD router kept for backward compatibility. Remove after clients migrate.
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(patents.router, prefix="/patents", tags=["Patents"])
router.include_router(ip_claims.router, prefix="/ip-claims", tags=["IP Claims"])
