"""
Patent verification endpoints.

According to IPChain MVP specification:
- POST /api/patents/precheck
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.patent import PatentPrecheckRequest, PatentPrecheckResponse
from app.services.patent_service import PatentService

router = APIRouter()


@router.post(
    "/precheck",
    response_model=PatentPrecheckResponse,
    summary="Patent pre-check",
)
async def patent_precheck(
    data: PatentPrecheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Proxy and normalize USPTO or external patent API lookup.
    
    Provides normalized response contract even if external
    provider responses vary. Expected outcomes:
    - found: patent found with confident match
    - not_found: patent record not found
    - partial: incomplete or ambiguous match
    - error: provider failed or timed out
    
    Requires authenticated user (issuer or admin role recommended).
    """
    patent_service = PatentService(db)
    
    result = await patent_service.precheck_patent(
        patent_number=data.patent_number,
        jurisdiction=data.jurisdiction or "US",
        claimed_owner=data.claimed_owner_name,
        actor_id=current_user.id,
    )
    
    return PatentPrecheckResponse(**result)
