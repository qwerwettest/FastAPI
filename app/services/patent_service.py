from datetime import datetime, timezone

from app.schemas.ip_claim import PatentPrecheckRequest, PatentPrecheckResponse


class PatentService:
    @staticmethod
    async def precheck(payload: PatentPrecheckRequest) -> PatentPrecheckResponse:
        normalized_number = payload.patent_number.strip().upper()

        if not normalized_number or len(normalized_number) < 3:
            return PatentPrecheckResponse(
                status="error",
                patent_number=normalized_number,
                prechecked=False,
                message="invalid patent number",
            )

        # MVP deterministic adapter. External USPTO integration can replace this logic.
        if normalized_number.endswith("404"):
            return PatentPrecheckResponse(
                status="not_found",
                patent_number=normalized_number,
                prechecked=False,
                message="patent not found",
            )

        if normalized_number.endswith("503"):
            return PatentPrecheckResponse(
                status="error",
                patent_number=normalized_number,
                prechecked=False,
                message="upstream provider unavailable",
            )

        if normalized_number.endswith("777"):
            return PatentPrecheckResponse(
                status="partial",
                patent_number=normalized_number,
                title=f"Patent {normalized_number}",
                owner=payload.claimed_owner_name,
                metadata={"checked_at": datetime.now(timezone.utc).isoformat(), "jurisdiction": payload.jurisdiction},
                source_id=f"uspto:{normalized_number}",
                prechecked=True,
                message="partial match; manual review required",
            )

        return PatentPrecheckResponse(
            status="found",
            patent_number=normalized_number,
            title=f"Patent {normalized_number}",
            owner=payload.claimed_owner_name,
            metadata={"checked_at": datetime.now(timezone.utc).isoformat(), "jurisdiction": payload.jurisdiction},
            source_id=f"uspto:{normalized_number}",
            prechecked=True,
            message="match found",
        )
