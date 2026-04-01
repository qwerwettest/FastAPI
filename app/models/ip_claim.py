"""
IP Claim, Document, and Review models.

Canonical schema according to IPChain MVP specification.
Replaces the legacy Patent model.
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String, DateTime, ForeignKey,
    Index, Text, UniqueConstraint, Enum as SAEnum, JSON,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums - Canonical values from specification
# ---------------------------------------------------------------------------

class IpClaimStatus(str, enum.Enum):
    """IP claim status lifecycle as per specification."""
    draft = "draft"
    submitted = "submitted"
    prechecked = "prechecked"
    awaiting_kyc = "awaiting_kyc"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"


class DocumentType(str, enum.Enum):
    """Document types for IP claims."""
    application = "application"
    grant = "grant"
    supporting = "supporting"
    ownership_proof = "ownership_proof"


class ReviewDecision(str, enum.Enum):
    """Review decision outcomes."""
    approve = "approve"
    reject = "reject"
    request_more_info = "request_more_info"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class IpClaim(Base):
    """
    IP ownership claim against a patent.
    
    Maps to: ip_claims table
    Contains enriched data from USPTO pre-check.
    """
    __tablename__ = "ip_claims"
    __table_args__ = (
        Index("ix_ip_claims_issuer_user_id", "issuer_user_id"),
        Index("ix_ip_claims_status", "status"),
        Index("ix_ip_claims_patent_number", "patent_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    issuer_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    patent_number: Mapped[str] = mapped_column(String(100), nullable=False)
    claimed_owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="US")
    
    # Status lifecycle
    status: Mapped[str] = mapped_column(
        SAEnum(*[s.value for s in IpClaimStatus], name="ip_claim_status"),
        nullable=False,
        default=IpClaimStatus.draft,
    )
    
    # Pre-check enrichment fields
    prechecked: Mapped[bool] = mapped_column(String(5), nullable=True, default=False)
    precheck_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    patent_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    patent_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    issuer: Mapped["User"] = relationship(
        "User", foreign_keys=[issuer_user_id], back_populates="ip_claims"
    )
    documents: Mapped[List["IpDocument"]] = relationship(
        "IpDocument", back_populates="ip_claim", cascade="all, delete-orphan"
    )
    reviews: Mapped[List["IpReview"]] = relationship(
        "IpReview", back_populates="ip_claim", cascade="all, delete-orphan"
    )
    asset: Mapped[Optional["Asset"]] = relationship(
        "Asset", back_populates="ip_claim", uselist=False, cascade="all, delete-orphan"
    )


class IpDocument(Base):
    """
    Supporting document for an IP claim.
    
    Maps to: ip_documents table
    Stores reference to S3/object storage, not file content.
    """
    __tablename__ = "ip_documents"
    __table_args__ = (
        Index("ix_ip_documents_ip_claim_id", "ip_claim_id"),
        Index("ix_ip_documents_uploaded_at", "uploaded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ip_claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ip_claims.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(
        SAEnum(*[d.value for d in DocumentType], name="document_type"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    ip_claim: Mapped["IpClaim"] = relationship(back_populates="documents")


class IpReview(Base):
    """
    Manual review decision for an IP claim.
    
    Maps to: ip_reviews table
    Records compliance/admin review decisions.
    """
    __tablename__ = "ip_reviews"
    __table_args__ = (
        Index("ix_ip_reviews_ip_claim_id", "ip_claim_id"),
        Index("ix_ip_reviews_reviewer_id", "reviewer_id"),
        Index("ix_ip_reviews_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ip_claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ip_claims.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[str] = mapped_column(
        SAEnum(*[d.value for d in ReviewDecision], name="review_decision"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    ip_claim: Mapped["IpClaim"] = relationship(back_populates="reviews")
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewer_id], back_populates="reviewed_claims"
    )


class Asset(Base):
    """
    Tokenizable asset backed by an approved IP claim.
    
    Maps to: assets table
    Created after IP claim approval, before tokenization.
    """
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_ip_claim_id", "ip_claim_id"),
        Index("ix_assets_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ip_claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ip_claims.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    legal_structure: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
        # Will use: draft, approved_for_tokenization, tokenized, listed, paused, archived
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    ip_claim: Mapped["IpClaim"] = relationship(back_populates="asset")
    token_issuance: Mapped[Optional["TokenIssuance"]] = relationship(
        "TokenIssuance", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    listings: Mapped[List["Listing"]] = relationship(
        "Listing", back_populates="asset", cascade="all, delete-orphan"
    )


class TokenIssuance(Base):
    """
    On-chain token issuance record.
    
    Maps to: token_issuances table
    Stores Solana mint address and supply info.
    """
    __tablename__ = "token_issuances"
    __table_args__ = (
        Index("ix_token_issuances_asset_id", "asset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    mint_address: Mapped[str] = mapped_column(String(100), nullable=False)
    network: Mapped[str] = mapped_column(String(50), nullable=False, default="solana-devnet")
    total_supply: Mapped[int] = mapped_column(nullable=False)
    decimals: Mapped[int] = mapped_column(nullable=False, default=9)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="token_issuance")


class Listing(Base):
    """
    Marketplace listing for an asset.
    
    Maps to: listings table
    """
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_asset_id", "asset_id"),
        Index("ix_listings_status", "listing_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    listing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
        # Will use: draft, active, paused, closed, cancelled
    )
    price_model: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="listings")
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="listing", cascade="all, delete-orphan"
    )


class Order(Base):
    """
    Purchase order for tokens.
    
    Maps to: orders table
    """
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_listing_id", "listing_id"),
        Index("ix_orders_buyer_user_id", "buyer_user_id"),
        Index("ix_orders_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    buyer_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    qty: Mapped[int] = mapped_column(nullable=False)
    amount_sol: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="created"
        # Will use: created, blocked_kyc_required, pending_compliance, approved, paid, failed, cancelled
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    listing: Mapped["Listing"] = relationship(back_populates="orders")
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_user_id], back_populates="orders"
    )
    trades: Mapped[List["Trade"]] = relationship(
        "Trade", back_populates="order", cascade="all, delete-orphan"
    )


class Trade(Base):
    """
    Executed trade (settlement).
    
    Maps to: trades table
    """
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_order_id", "order_id"),
        Index("ix_trades_settled_at", "settled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    tx_signature: Mapped[str] = mapped_column(String(200), nullable=False)
    settled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    settlement_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
        # Will use: pending, settled, failed, reversed
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="trades")
