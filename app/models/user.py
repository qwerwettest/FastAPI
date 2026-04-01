"""
User and related identity models.

Canonical schema according to IPChain MVP specification.
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey,
    Index, Text, UniqueConstraint, Enum as SAEnum, JSON,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ip_claim import Order


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums - Canonical values from specification
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    """User roles as per specification."""
    user = "user"
    issuer = "issuer"
    investor = "investor"
    compliance_officer = "compliance_officer"
    admin = "admin"


class UserStatus(str, enum.Enum):
    """User status lifecycle."""
    pending_email_verification = "pending_email_verification"
    active = "active"
    suspended = "suspended"
    blocked = "blocked"


class KYCCaseStatus(str, enum.Enum):
    """KYC case status lifecycle."""
    not_started = "not_started"
    pending = "pending"
    needs_input = "needs_input"
    manual_review = "manual_review"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class SanctionCheckStatus(str, enum.Enum):
    """Sanction check status."""
    pending = "pending"
    clear = "clear"
    matches_found = "matches_found"
    manual_review = "manual_review"
    failed = "failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    """
    User identity record.
    
    Maps to: users table
    PII fields: email (should be encrypted at rest in production)
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_status", "status"),
        Index("ix_users_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        SAEnum(*[r.value for r in UserRole], name="user_role"),
        nullable=False,
        default=UserRole.user,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(*[s.value for s in UserStatus], name="user_status"),
        nullable=False,
        default=UserStatus.pending_email_verification,
    )
    wallet_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships - 1:1 or 1:many
    profile: Mapped[Optional["Profile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    kyc_cases: Mapped[List["KYCCase"]] = relationship(
        "KYCCase", back_populates="user", cascade="all, delete-orphan"
    )
    sanctions_checks: Mapped[List["SanctionCheck"]] = relationship(
        "SanctionCheck", back_populates="user", cascade="all, delete-orphan"
    )
    wallet_links: Mapped[List["WalletLink"]] = relationship(
        "WalletLink", back_populates="user", cascade="all, delete-orphan"
    )
    ip_claims: Mapped[List["IpClaim"]] = relationship(
        "IpClaim", back_populates="issuer", cascade="all, delete-orphan"
    )
    reviewed_claims: Mapped[List["IpReview"]] = relationship(
        "IpReview", back_populates="reviewer", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="buyer", cascade="all, delete-orphan"
    )


class Profile(Base):
    """
    User profile - extended identity information.
    
    Maps to: profiles table
    PII fields: legal_name, dob, address
    """
    __tablename__ = "profiles"
    __table_args__ = (
        Index("ix_profiles_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dob: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class KYCCase(Base):
    """
    KYC verification case for a user.
    
    Maps to: kyc_cases table
    PII: review_result may contain sensitive data
    """
    __tablename__ = "kyc_cases"
    __table_args__ = (
        UniqueConstraint("provider", "provider_case_id", name="uq_kyc_cases_provider_case"),
        Index("ix_kyc_cases_user_id", "user_id"),
        Index("ix_kyc_cases_provider_case", "provider", "provider_case_id"),
        Index("ix_kyc_cases_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_case_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(*[s.value for s in KYCCaseStatus], name="kyc_case_status"),
        nullable=False,
        default=KYCCaseStatus.not_started,
    )
    review_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="kyc_cases")


class SanctionCheck(Base):
    """
    Sanctions/risk screening record.
    
    Maps to: sanctions_checks table
    """
    __tablename__ = "sanctions_checks"
    __table_args__ = (
        Index("ix_sanctions_checks_user_id", "user_id"),
        Index("ix_sanctions_checks_checked_at", "checked_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum(*[s.value for s in SanctionCheckStatus], name="sanction_check_status"),
        nullable=False,
        default=SanctionCheckStatus.pending,
    )
    flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="sanctions_checks")


class WalletLink(Base):
    """
    User wallet address linkage.
    
    Maps to: wallet_links table
    """
    __tablename__ = "wallet_links"
    __table_args__ = (
        UniqueConstraint("wallet_address", "network", name="uq_wallet_links_address_network"),
        Index("ix_wallet_links_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    wallet_address: Mapped[str] = mapped_column(String(100), nullable=False)
    network: Mapped[str] = mapped_column(String(50), nullable=False, default="solana")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="wallet_links")
