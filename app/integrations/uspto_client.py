"""
USPTO API client integration.

Provides patent lookup and verification capabilities.
For MVP: mocks external API calls with simulated responses.
"""
import httpx
from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings


class PatentPrecheckStatus(str, Enum):
    """Normalized patent pre-check outcomes."""
    FOUND = "found"
    NOT_FOUND = "not_found"
    PARTIAL = "partial"
    ERROR = "error"


class PatentData:
    """Normalized patent data structure."""

    def __init__(
        self,
        patent_number: str,
        title: str,
        owner: str,
        metadata: Dict[str, Any],
        source_id: str,
    ):
        self.patent_number = patent_number
        self.title = title
        self.owner = owner
        self.metadata = metadata
        self.source_id = source_id


class USPTOClient:
    """
    Client for USPTO Patent API.
    
    In production: integrate with actual USPTO API or equivalent patent registry.
    For MVP: provides mock responses for development and testing.
    """

    def __init__(self):
        self.base_url = settings.USPTO_API_URL
        self.timeout = settings.USPTO_API_TIMEOUT
        self.api_key = settings.USPTO_API_KEY

    async def lookup_patent(
        self,
        patent_number: str,
        jurisdiction: str = "US",
    ) -> tuple[PatentPrecheckStatus, Optional[PatentData]]:
        """
        Look up a patent by number.
        
        Returns:
            Tuple of (status, patent_data)
            - status: FOUND, NOT_FOUND, PARTIAL, or ERROR
            - patent_data: normalized patent info if found/partial
        """
        # TODO: Replace with actual USPTO API integration
        # For MVP: simulate responses based on patent number patterns
        
        return await self._mock_lookup(patent_number, jurisdiction)

    async def _mock_lookup(
        self,
        patent_number: str,
        jurisdiction: str,
    ) -> tuple[PatentPrecheckStatus, Optional[PatentData]]:
        """Mock patent lookup for MVP development."""
        
        # Simulate different scenarios for testing
        if patent_number.startswith("999"):
            # Simulate not found
            return PatentPrecheckStatus.NOT_FOUND, None
        
        elif patent_number.startswith("888"):
            # Simulate partial match
            return PatentPrecheckStatus.PARTIAL, PatentData(
                patent_number=patent_number,
                title="Partial Match Patent",
                owner="Unknown Owner",
                metadata={"incomplete": True},
                source_id=f"mock-{patent_number}",
            )
        
        elif patent_number.startswith("777"):
            # Simulate external API error
            return PatentPrecheckStatus.ERROR, None
        
        else:
            # Simulate successful found
            return PatentPrecheckStatus.FOUND, PatentData(
                patent_number=patent_number,
                title=f"Patent {patent_number} - Sample Technology",
                owner="Sample Owner Inc.",
                metadata={
                    "filing_date": "2020-01-15",
                    "grant_date": "2022-06-20",
                    "status": "active",
                    "jurisdiction": jurisdiction,
                },
                source_id=f"uspto-{patent_number}",
            )

    async def verify_patent_ownership(
        self,
        patent_number: str,
        claimed_owner: str,
    ) -> bool:
        """
        Verify that the claimed owner matches patent records.
        
        Returns True if ownership is confirmed or cannot be verified.
        """
        status, patent_data = await self.lookup_patent(patent_number)
        
        if status == PatentPrecheckStatus.NOT_FOUND:
            return False
        
        if patent_data is None:
            return True  # Cannot verify, defer to manual review
        
        # Normalize names for comparison
        patent_owner = patent_data.owner.lower().strip()
        claimed = claimed_owner.lower().strip()
        
        return claimed in patent_owner or patent_owner in claimed


# Singleton instance
uspto_client = USPTOClient()
