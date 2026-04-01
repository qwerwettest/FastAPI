"""
Patent verification schemas - request/response DTOs.

According to IPChain MVP specification.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


# ---------------------------------------------------------------------------
# Patent Pre-check schemas
# ---------------------------------------------------------------------------

class PatentPrecheckRequest(BaseModel):
    """
    Patent pre-check request.
    
    Contains patent number as required field
    and optional context fields.
    """
    patent_number: str = Field(..., description="Patent number to lookup")
    jurisdiction: Optional[str] = Field("US", description="Patent jurisdiction")
    claimed_owner_name: Optional[str] = Field(None, description="Claimed owner name")


class PatentPrecheckResponse(BaseModel):
    """
    Patent pre-check response.
    
    Returns normalized status value from set:
    found, not_found, partial, error
    
    Together with patent metadata when available.
    """
    status: str = Field(
        ...,
        description="Normalized status: found, not_found, partial, error",
        examples=["found", "not_found", "partial", "error"],
    )
    patent_number: str
    title: Optional[str] = None
    owner: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    prechecked: bool = Field(
        ...,
        description="Whether patent data was successfully retrieved",
    )
    message: Optional[str] = None

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "status": "found",
                "patent_number": "US12345678B2",
                "title": "Sample Technology Patent",
                "owner": "Example Corp",
                "metadata": {"filing_date": "2020-01-15", "status": "active"},
                "source_id": "uspto-US12345678B2",
                "prechecked": True,
                "message": "Патент найден",
            },
            {
                "status": "not_found",
                "patent_number": "US99999999B2",
                "title": None,
                "owner": None,
                "metadata": None,
                "source_id": None,
                "prechecked": False,
                "message": "Патент не найден",
            },
        ]
    }}
