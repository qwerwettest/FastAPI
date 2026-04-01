"""
Patent verification service.

Handles USPTO API integration and patent pre-check workflow.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.uspto_client import (
    USPTOClient,
    PatentPrecheckStatus,
    PatentData,
)
from app.repositories.audit_log_repository import AuditLogRepository


class PatentService:
    """Service for patent verification and pre-check."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.uspto_client = USPTOClient()
        self.audit_repo = AuditLogRepository(session)

    async def precheck_patent(
        self,
        patent_number: str,
        jurisdiction: str = "US",
        claimed_owner: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform patent pre-check via USPTO API.
        
        Args:
            patent_number: Patent number to lookup
            jurisdiction: Patent jurisdiction (default: US)
            claimed_owner: Claimed owner name for verification
            actor_id: User ID performing the action (for audit)
        
        Returns:
            Normalized pre-check result with status and patent data
        """
        status, patent_data = await self.uspto_client.lookup_patent(
            patent_number, jurisdiction
        )
        
        # Build response
        result = self._build_precheck_result(
            status=status,
            patent_data=patent_data,
            patent_number=patent_number,
            jurisdiction=jurisdiction,
        )
        
        # Audit log
        await self.audit_repo.create(
            actor_id=actor_id,
            action="patent_precheck",
            entity_type="ip_claim",
            entity_id=None,
            payload={
                "patent_number": patent_number,
                "jurisdiction": jurisdiction,
                "precheck_status": status.value,
            },
        )
        
        return result

    def _build_precheck_result(
        self,
        status: PatentPrecheckStatus,
        patent_data: Optional[PatentData],
        patent_number: str,
        jurisdiction: str,
    ) -> Dict[str, Any]:
        """Build normalized pre-check response."""
        
        if status == PatentPrecheckStatus.FOUND and patent_data:
            return {
                "status": PatentPrecheckStatus.FOUND.value,
                "patent_number": patent_data.patent_number,
                "title": patent_data.title,
                "owner": patent_data.owner,
                "metadata": patent_data.metadata,
                "source_id": patent_data.source_id,
                "prechecked": True,
                "message": "Патент найден",
            }
        
        elif status == PatentPrecheckStatus.PARTIAL and patent_data:
            return {
                "status": PatentPrecheckStatus.PARTIAL.value,
                "patent_number": patent_data.patent_number,
                "title": patent_data.title,
                "owner": patent_data.owner,
                "metadata": patent_data.metadata,
                "source_id": patent_data.source_id,
                "prechecked": True,
                "message": "Найдено частичное совпадение, требуется ручная проверка",
            }
        
        elif status == PatentPrecheckStatus.NOT_FOUND:
            return {
                "status": PatentPrecheckStatus.NOT_FOUND.value,
                "patent_number": patent_number,
                "title": None,
                "owner": None,
                "metadata": None,
                "source_id": None,
                "prechecked": False,
                "message": "Патент не найден",
            }
        
        else:  # ERROR
            return {
                "status": PatentPrecheckStatus.ERROR.value,
                "patent_number": patent_number,
                "title": None,
                "owner": None,
                "metadata": None,
                "source_id": None,
                "prechecked": False,
                "message": "Ошибка внешнего API",
            }

    async def verify_ownership(
        self,
        patent_number: str,
        claimed_owner: str,
    ) -> bool:
        """
        Verify patent ownership matches claimed owner.
        
        Returns True if ownership is confirmed or cannot be verified (defer to manual review).
        """
        return await self.uspto_client.verify_patent_ownership(
            patent_number, claimed_owner
        )
