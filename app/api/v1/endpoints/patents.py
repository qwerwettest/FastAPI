from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ip_claim import PatentPrecheckRequest, PatentPrecheckResponse
from app.services.patent_service import PatentService

router = APIRouter()


@router.post("/precheck", response_model=PatentPrecheckResponse)
async def patent_precheck(
    payload: PatentPrecheckRequest,
    _: User = Depends(get_current_user),
):
    return await PatentService.precheck(payload)
