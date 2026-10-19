from typing import Annotated

from fastapi import APIRouter, Path, status

from app.core.dependencies import ClaimReviewServiceDep, ReviewerDep
from app.schemas.claim_review_response import ClaimReviewResponse

router = APIRouter(prefix="/claims", tags=["claim reviews"])

ClaimIdPath = Annotated[str, Path(min_length=36, max_length=36)]


@router.post(
    "/{claim_id}/ai-reviews",
    response_model=ClaimReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_ai_review(
    claim_id: ClaimIdPath,
    reviewer: ReviewerDep,
    claim_review_service: ClaimReviewServiceDep,
) -> ClaimReviewResponse:
    review = await claim_review_service.run_review(claim_id, reviewer)
    return ClaimReviewResponse.model_validate(review)


@router.get("/{claim_id}/ai-reviews/latest", response_model=ClaimReviewResponse)
async def get_latest_ai_review(
    claim_id: ClaimIdPath,
    reviewer: ReviewerDep,
    claim_review_service: ClaimReviewServiceDep,
) -> ClaimReviewResponse:
    review = await claim_review_service.get_latest_review(claim_id, reviewer)
    return ClaimReviewResponse.model_validate(review)
