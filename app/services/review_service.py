"""
Review service.

Handles manual review workflow for IP claims.
"""
import uuid
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ip_claim import IpClaim, IpClaimStatus, ReviewDecision
from app.repositories.ip_claim_repository import IpClaimRepository
from app.repositories.audit_log_repository import AuditLogRepository


class ReviewService:
    """Service for IP Claim review operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ip_claim_repo = IpClaimRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def submit_review(
        self,
        claim_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        decision: ReviewDecision,
        notes: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> IpClaim:
        """
        Submit review decision for an IP claim.
        
        Args:
            claim_id: Claim ID to review
            reviewer_id: Reviewer user ID
            decision: Review decision (approve/reject/request_more_info)
            notes: Optional review notes
            actor_id: User ID performing the action (for audit)
        
        Returns:
            Updated IP claim
        
        Raises:
            HTTPException: If claim not found
        """
        from fastapi import HTTPException, status
        
        claim = await self.ip_claim_repo.get_by_id(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IP-заявка не найдена",
            )
        
        # Store old status for audit
        old_status = claim.status
        
        # Add review record
        await self.ip_claim_repo.add_review(
            claim_id=claim_id,
            reviewer_id=reviewer_id,
            decision=decision,
            notes=notes,
        )
        
        # Update claim status based on decision
        new_status = self._get_status_from_decision(decision)
        await self.ip_claim_repo.update_status(claim, new_status)
        
        # Audit log
        await self.audit_repo.create(
            actor_id=actor_id,
            action="ip_claim_reviewed",
            entity_type="ip_claim",
            entity_id=str(claim_id),
            payload={
                "reviewer_id": str(reviewer_id),
                "decision": decision.value,
                "old_status": old_status,
                "new_status": new_status.value,
                "notes": notes,
            },
        )
        
        return claim

    def _get_status_from_decision(
        self, decision: ReviewDecision
    ) -> IpClaimStatus:
        """Map review decision to claim status."""
        if decision == ReviewDecision.approve:
            return IpClaimStatus.approved
        elif decision == ReviewDecision.reject:
            return IpClaimStatus.rejected
        else:  # request_more_info
            return IpClaimStatus.under_review

    async def get_claim_reviews(
        self,
        claim_id: uuid.UUID,
    ) -> list[Dict[str, Any]]:
        """Get all reviews for a claim."""
        reviews = await self.ip_claim_repo.get_reviews_by_claim(claim_id)
        return [
            {
                "id": review.id,
                "ip_claim_id": review.ip_claim_id,
                "reviewer_id": review.reviewer_id,
                "decision": review.decision,
                "notes": review.notes,
                "created_at": review.created_at,
            }
            for review in reviews
        ]
