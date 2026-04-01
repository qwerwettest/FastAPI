"""
IP Claim service.

Handles IP claim creation, status workflow, and document management.
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ip_claim import IpClaim, IpClaimStatus, DocumentType
from app.repositories.ip_claim_repository import IpClaimRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.patent_service import PatentService
from app.core.config import settings


class IpClaimService:
    """Service for IP Claim operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ip_claim_repo = IpClaimRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.patent_service = PatentService(session)

    async def create_claim(
        self,
        issuer_user_id: uuid.UUID,
        patent_number: str,
        claimed_owner_name: str,
        title: str,
        description: Optional[str] = None,
        jurisdiction: str = "US",
        precheck_snapshot: Optional[Dict[str, Any]] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> IpClaim:
        """
        Create a new IP claim.
        
        Args:
            issuer_user_id: User ID of the claim issuer
            patent_number: Patent number
            claimed_owner_name: Claimed owner name
            title: Patent title
            description: Optional description
            jurisdiction: Patent jurisdiction
            precheck_snapshot: Optional pre-check result snapshot
            actor_id: User ID performing the action (for audit)
        
        Returns:
            Created IP claim
        """
        # Perform pre-check if not provided
        if precheck_snapshot is None:
            precheck_result = await self.patent_service.precheck_patent(
                patent_number=patent_number,
                jurisdiction=jurisdiction,
                claimed_owner=claimed_owner_name,
                actor_id=str(actor_id) if actor_id else None,
            )
            precheck_snapshot = precheck_result
        
        # Determine initial status based on pre-check
        precheck_status = precheck_snapshot.get("status")
        if precheck_status == "found":
            initial_status = IpClaimStatus.prechecked
        elif precheck_status == "partial":
            initial_status = IpClaimStatus.submitted  # Requires manual review
        else:
            initial_status = IpClaimStatus.draft
        
        # Create claim
        claim = IpClaim(
            issuer_user_id=issuer_user_id,
            patent_number=patent_number,
            claimed_owner_name=claimed_owner_name,
            title=title,
            description=description,
            jurisdiction=jurisdiction,
            status=initial_status.value,
            prechecked=precheck_snapshot.get("prechecked", False),
            precheck_status=precheck_status,
            patent_owner=precheck_snapshot.get("owner"),
            patent_metadata=precheck_snapshot.get("metadata"),
            source_id=precheck_snapshot.get("source_id"),
            checked_at=datetime.now(timezone.utc) if precheck_snapshot.get("prechecked") else None,
        )
        
        created = await self.ip_claim_repo.create(claim)
        
        # Audit log
        await self.audit_repo.create(
            actor_id=actor_id,
            action="ip_claim_created",
            entity_type="ip_claim",
            entity_id=str(created.id),
            payload={
                "patent_number": patent_number,
                "initial_status": initial_status.value,
            },
        )
        
        return created

    async def get_claim(
        self,
        claim_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
    ) -> IpClaim:
        """
        Get IP claim by ID with access control.
        
        Args:
            claim_id: Claim ID
            user_id: Requesting user ID
            user_role: Requesting user role
        
        Returns:
            IP claim
        
        Raises:
            HTTPException: If claim not found or access denied
        """
        claim = await self.ip_claim_repo.get_by_id(claim_id)
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IP-заявка не найдена",
            )
        
        # Access control: owner, admin, or compliance officer
        allowed_roles = {"admin", "compliance_officer"}
        if claim.issuer_user_id != user_id and user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен",
            )
        
        return claim

    async def get_claims_for_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[int, List[IpClaim]]:
        """Get all claims for a user."""
        return await self.ip_claim_repo.get_by_issuer(
            issuer_user_id=user_id,
            skip=skip,
            limit=limit,
        )

    async def upload_document(
        self,
        claim_id: uuid.UUID,
        file: UploadFile,
        document_type: Optional[DocumentType] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Upload supporting document for IP claim.
        
        Args:
            claim_id: Claim ID
            file: Uploaded file
            document_type: Document type
            actor_id: User ID performing the action
        
        Returns:
            Document metadata
        
        Raises:
            HTTPException: If claim not found or file validation fails
        """
        # Verify claim exists
        claim = await self.ip_claim_repo.get_by_id(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IP-заявка не найдена",
            )
        
        # Validate file
        await self._validate_document(file)
        
        # In production: upload to S3/object storage
        # For MVP: store local path reference
        file_url = f"/storage/{claim_id}/{file.filename}"
        
        # Add document
        document = await self.ip_claim_repo.add_document(
            claim_id=claim_id,
            file_url=file_url,
            document_type=document_type,
        )
        
        # Audit log
        await self.audit_repo.create(
            actor_id=actor_id,
            action="document_uploaded",
            entity_type="ip_claim",
            entity_id=str(claim_id),
            payload={
                "document_id": str(document.id),
                "document_type": document_type.value if document_type else None,
                "file_name": file.filename,
            },
        )
        
        return {
            "id": document.id,
            "ip_claim_id": claim_id,
            "file_url": file_url,
            "document_type": document.document_type,
            "uploaded_at": document.uploaded_at,
        }

    async def _validate_document(self, file: UploadFile) -> None:
        """Validate uploaded document."""
        # Check file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл слишком большой (максимум {settings.MAX_FILE_SIZE_MB}MB)",
            )
        
        # Check file type
        if file.content_type not in settings.ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый тип файла: {file.content_type}",
            )
        
        # Reset file pointer for later reading
        await file.seek(0)
