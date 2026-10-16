from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.claim_status import ClaimStatus
from app.repositories.base_repository import BaseRepository


class ClaimRepository(BaseRepository[Claim]):
    """Data access for claims."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Claim)

    async def list_claims(
        self,
        *,
        submitter_id: str | None,
        status: ClaimStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Claim], int]:
        """Return one page of claims (newest first) and the total match count."""
        conditions: list[ColumnElement[bool]] = []
        if submitter_id is not None:
            conditions.append(Claim.submitted_by == submitter_id)
        if status is not None:
            conditions.append(Claim.status == status)

        total = await self._session.scalar(
            select(func.count()).select_from(Claim).where(*conditions)
        )
        result = await self._session.execute(
            select(Claim)
            .where(*conditions)
            .order_by(Claim.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total or 0

    async def save(self, claim: Claim) -> Claim:
        """Persist changes made to an already loaded claim."""
        await self._session.flush()
        await self._session.refresh(claim)
        return claim
