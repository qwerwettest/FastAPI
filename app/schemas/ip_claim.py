"""
IP Claim schemas - request/response DTOs.

According to IPChain MVP specification.
"""
import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.models.ip_claim import IpClaimStatus, DocumentType


# ---------------------------------------------------------------------------
# IP Claim request schemas
# ---------------------------------------------------------------------------

class CreateIpClaimRequest(BaseModel):
    """
    IP claim creation request.
    
    Includes patent number, optional patent title,
    claimed owner name, description, jurisdiction,
    and optional pre-check snapshot.
    """
    patent_number: str = Field(..., description="Patent number")
    claimed_owner_name: str = Field(..., description="Claimed owner name")
    title: str = Field(..., description="Patent title")
    description: Optional[str] = Field(None, description="Optional description")
    jurisdiction: Optional[str] = Field("US", description="Patent jurisdiction")
    precheck_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pre-check result snapshot",
    )


class IpClaimFilterRequest(BaseModel):
    """IP claim list filter."""
    status: Optional[IpClaimStatus] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


# ---------------------------------------------------------------------------
# IP Claim response schemas
# ---------------------------------------------------------------------------

class IpClaimResponse(BaseModel):
    """
    IP claim response.
    
    Returns claim identifier, issuer user identifier,
    patent number, patent title, claimed owner name,
    description, jurisdiction, claim status, prechecked flag,
    patent metadata, and timestamps.
    """
    id: uuid.UUID
    issuer_user_id: uuid.UUID
    patent_number: str
    claimed_owner_name: str
    title: str
    description: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: IpClaimStatus
    prechecked: bool
    precheck_status: Optional[str] = None
    patent_owner: Optional[str] = None
    patent_metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IpClaimListResponse(BaseModel):
    """IP claim list response."""
    total: int
    items: List[IpClaimResponse]


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------

class UploadDocumentResponse(BaseModel):
    """
    Uploaded document response.
    
    Returns uploaded document identifier,
    related claim identifier, file URL or storage key,
    document type, and upload timestamp.
    """
    id: uuid.UUID
    ip_claim_id: uuid.UUID
    file_url: str
    document_type: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Document list response."""
    total: int
    items: List[UploadDocumentResponse]


# ---------------------------------------------------------------------------
# Review schemas
# ---------------------------------------------------------------------------

class IpClaimReviewRequest(BaseModel):
    """
    IP claim review request.
    
    Contains decision field with values:
    approve, reject, request_more_info
    
    Plus optional review notes.
    """
    decision: str = Field(
        ...,
        description="Review decision: approve, reject, request_more_info",
        pattern="^(approve|reject|request_more_info)$",
    )
    notes: Optional[str] = Field(None, description="Optional review notes")


class IpReviewResponse(BaseModel):
    """IP review response."""
    id: uuid.UUID
    ip_claim_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
