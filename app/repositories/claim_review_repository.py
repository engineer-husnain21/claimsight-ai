from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_review import ClaimReview
from app.repositories.base_repository import BaseRepository


class ClaimReviewRepository(BaseRepository[ClaimReview]):
    """Data access for AI claim reviews."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ClaimReview)

    async def get_latest_for_claim(self, claim_id: str) -> ClaimReview | None:
        """Return the newest review for a claim, or None if it was never reviewed."""
        result = await self._session.execute(
            select(ClaimReview)
            .where(ClaimReview.claim_id == claim_id)
            .order_by(ClaimReview.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()
