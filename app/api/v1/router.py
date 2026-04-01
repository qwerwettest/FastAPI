"""
API v1 router configuration.

According to IPChain MVP specification.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, patents, ip_claims

router = APIRouter()


@router.get("/ping", tags=["Utils"])
async def ping():
    """Health check endpoint."""
    return {"message": "pong"}


# Register endpoints according to specification
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

router.include_router(
    patents.router,
    prefix="/patents",
    tags=["Patents"],
)

router.include_router(
    ip_claims.router,
    prefix="/ip-claims",
    tags=["IP Claims"],
)
