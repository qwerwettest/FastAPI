"""
IP Claims endpoints.

According to IPChain MVP specification:
- POST /api/ip-claims
- GET /api/ip-claims
- GET /api/ip-claims/{id}
- POST /api/ip-claims/{id}/documents
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.ip_claim import DocumentType, IpClaimStatus
from app.schemas.ip_claim import (
    CreateIpClaimRequest,
    IpClaimResponse,
    IpClaimListResponse,
    UploadDocumentResponse,
    IpClaimReviewRequest,
    IpReviewResponse,
)
from app.services.ip_claim_service import IpClaimService
from app.services.review_service import ReviewService

router = APIRouter()


@router.post(
    "/",
    response_model=IpClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create IP claim",
)
async def create_ip_claim(
    data: CreateIpClaimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new IP claim for a patent.
    
    Requires authenticated user with issuer or allowed equivalent role.
    Performs patent pre-check automatically if not provided.
    """
    # Check role - only issuer, admin can create claims
    if current_user.role not in {UserRole.issuer.value, UserRole.admin.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль issuer или admin",
        )
    
    ip_claim_service = IpClaimService(db)
    
    claim = await ip_claim_service.create_claim(
        issuer_user_id=current_user.id,
        patent_number=data.patent_number,
        claimed_owner_name=data.claimed_owner_name,
        title=data.title,
        description=data.description,
        jurisdiction=data.jurisdiction or "US",
        precheck_snapshot=data.precheck_snapshot,
        actor_id=current_user.id,
    )
    
    return IpClaimResponse.model_validate(claim)


@router.get(
    "/",
    response_model=IpClaimListResponse,
    summary="List IP claims",
)
async def list_ip_claims(
    status_filter: Optional[IpClaimStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List IP claims with filters.
    
    Supports status filtering for issuer dashboards
    and admin review queues.
    """
    ip_claim_service = IpClaimService(db)
    
    # If regular user, show only their claims
    if current_user.role not in {UserRole.admin.value, UserRole.compliance_officer.value}:
        total, claims = await ip_claim_service.get_claims_for_user(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    else:
        # Admin can see all claims
        total, claims = await ip_claim_service.ip_claim_repo.get_all(
            skip=skip,
            limit=limit,
            status=status_filter,
        )
    
    return IpClaimListResponse(
        total=total,
        items=[IpClaimResponse.model_validate(c) for c in claims],
    )


@router.get(
    "/{claim_id}",
    response_model=IpClaimResponse,
    summary="Get IP claim details",
)
async def get_ip_claim(
    claim_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return claim details.
    
    Requires owner or reviewer role for access.
    """
    ip_claim_service = IpClaimService(db)
    
    claim = await ip_claim_service.get_claim(
        claim_id=claim_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    
    return IpClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/documents",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload supporting document",
)
async def upload_document(
    claim_id: uuid.UUID,
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload supporting claim documents.
    
    Requires owner role. Files are stored in private object storage.
    Supported types: PDF, JPEG, PNG. Max size: 10MB.
    """
    ip_claim_service = IpClaimService(db)
    
    # Verify ownership
    claim = await ip_claim_service.ip_claim_repo.get_by_id(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP-заявка не найдена",
        )
    
    if claim.issuer_user_id != current_user.id and current_user.role not in {UserRole.admin.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль владельца",
        )
    
    result = await ip_claim_service.upload_document(
        claim_id=claim_id,
        file=file,
        document_type=document_type,
        actor_id=current_user.id,
    )
    
    return UploadDocumentResponse(**result)


@router.post(
    "/{claim_id}/review",
    response_model=IpClaimResponse,
    summary="Apply review decision",
)
async def apply_review_decision(
    claim_id: uuid.UUID,
    data: IpClaimReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply admin review decision.
    
    Requires admin or compliance role.
    Decision values: approve, reject, request_more_info.
    Updates claim status and logs to audit trail.
    """
    # Check role
    if current_user.role not in {UserRole.admin.value, UserRole.compliance_officer.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль admin или compliance_officer",
        )
    
    # Map decision string to enum
    decision_map = {
        "approve": ReviewDecision.approve,
        "reject": ReviewDecision.reject,
        "request_more_info": ReviewDecision.request_more_info,
    }
    
    decision = decision_map.get(data.decision)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое решение: {data.decision}",
        )
    
    review_service = ReviewService(db)
    
    claim = await review_service.submit_review(
        claim_id=claim_id,
        reviewer_id=current_user.id,
        decision=decision,
        notes=data.notes,
        actor_id=current_user.id,
    )
    
    return IpClaimResponse.model_validate(claim)
