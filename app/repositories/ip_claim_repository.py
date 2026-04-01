"""
IP Claim repository - data access layer for IpClaim, IpDocument, IpReview entities.
"""
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ip_claim import (
    IpClaim,
    IpDocument,
    IpReview,
    IpClaimStatus,
    DocumentType,
    ReviewDecision,
)


class IpClaimRepository:
    """Repository for IP Claim operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, claim_id: uuid.UUID) -> Optional[IpClaim]:
        """Get IP claim by ID with documents and reviews loaded."""
        result = await self.session.execute(
            select(IpClaim)
            .options(
                selectinload(IpClaim.documents),
                selectinload(IpClaim.reviews),
            )
            .where(IpClaim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_issuer(
        self, claim_id: uuid.UUID
    ) -> Optional[IpClaim]:
        """Get IP claim by ID with issuer loaded."""
        result = await self.session.execute(
            select(IpClaim)
            .options(selectinload(IpClaim.issuer))
            .where(IpClaim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def get_by_issuer(
        self,
        issuer_user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[int, List[IpClaim]]:
        """Get IP claims by issuer with pagination."""
        total_result = await self.session.execute(
            select(func.count()).where(IpClaim.issuer_user_id == issuer_user_id)
        )
        total = total_result.scalar() or 0

        result = await self.session.execute(
            select(IpClaim)
            .where(IpClaim.issuer_user_id == issuer_user_id)
            .offset(skip)
            .limit(limit)
        )
        claims = result.scalars().all()
        return total, claims

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[IpClaimStatus] = None,
    ) -> tuple[int, List[IpClaim]]:
        """Get all IP claims with optional status filter."""
        query = select(IpClaim)
        count_query = select(func.count()).select_from(IpClaim)

        if status:
            query = query.where(IpClaim.status == status.value)
            count_query = count_query.where(IpClaim.status == status.value)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        claims = result.scalars().all()
        return total, claims

    async def create(self, claim: IpClaim) -> IpClaim:
        """Create a new IP claim."""
        self.session.add(claim)
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def update(self, claim: IpClaim, **kwargs) -> IpClaim:
        """Update IP claim fields."""
        for field, value in kwargs.items():
            if hasattr(claim, field):
                setattr(claim, field, value)
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def update_status(
        self, claim: IpClaim, status: IpClaimStatus
    ) -> IpClaim:
        """Update IP claim status."""
        claim.status = status.value
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def delete(self, claim: IpClaim) -> None:
        """Delete IP claim."""
        await self.session.delete(claim)
        await self.session.flush()

    # Document operations

    async def add_document(
        self,
        claim_id: uuid.UUID,
        file_url: str,
        document_type: Optional[DocumentType] = None,
    ) -> IpDocument:
        """Add a document to an IP claim."""
        document = IpDocument(
            ip_claim_id=claim_id,
            file_url=file_url,
            document_type=document_type.value if document_type else None,
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_document(
        self, document_id: uuid.UUID
    ) -> Optional[IpDocument]:
        """Get document by ID."""
        result = await self.session.execute(
            select(IpDocument).where(IpDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_documents_by_claim(
        self, claim_id: uuid.UUID
    ) -> List[IpDocument]:
        """Get all documents for a claim."""
        result = await self.session.execute(
            select(IpDocument).where(IpDocument.ip_claim_id == claim_id)
        )
        return result.scalars().all()

    # Review operations

    async def add_review(
        self,
        claim_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        decision: ReviewDecision,
        notes: Optional[str] = None,
    ) -> IpReview:
        """Add a review to an IP claim."""
        review = IpReview(
            ip_claim_id=claim_id,
            reviewer_id=reviewer_id,
            decision=decision.value,
            notes=notes,
        )
        self.session.add(review)
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def get_reviews_by_claim(
        self, claim_id: uuid.UUID
    ) -> List[IpReview]:
        """Get all reviews for a claim."""
        result = await self.session.execute(
            select(IpReview).where(IpReview.ip_claim_id == claim_id)
        )
        return result.scalars().all()

    async def get_latest_review(
        self, claim_id: uuid.UUID
    ) -> Optional[IpReview]:
        """Get the most recent review for a claim."""
        result = await self.session.execute(
            select(IpReview)
            .where(IpReview.ip_claim_id == claim_id)
            .order_by(IpReview.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
