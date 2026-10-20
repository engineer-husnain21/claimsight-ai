from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.core.dependencies import ClaimServiceDep, CurrentUserDep, ReviewerDep
from app.models.claim_status import ClaimStatus
from app.schemas.claim_list_response import ClaimListResponse
from app.schemas.claim_response import ClaimResponse
from app.schemas.claim_stats_response import ClaimStatsResponse
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.review_claim_request import ReviewClaimRequest

router = APIRouter(prefix="/claims", tags=["claims"])

ClaimIdPath = Annotated[str, Path(min_length=36, max_length=36)]


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    request: CreateClaimRequest,
    current_user: CurrentUserDep,
    claim_service: ClaimServiceDep,
) -> ClaimResponse:
    claim = await claim_service.create_claim(request, current_user)
    return ClaimResponse.model_validate(claim)


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    current_user: CurrentUserDep,
    claim_service: ClaimServiceDep,
    status_filter: Annotated[ClaimStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClaimListResponse:
    claims, total = await claim_service.list_claims(current_user, status_filter, limit, offset)
    return ClaimListResponse(
        items=[ClaimResponse.model_validate(claim) for claim in claims],
        total=total,
        limit=limit,
        offset=offset,
    )


# Must stay above "/{claim_id}", otherwise "stats" is parsed as a claim id.
@router.get("/stats", response_model=ClaimStatsResponse)
async def get_claim_stats(
    current_user: CurrentUserDep,
    claim_service: ClaimServiceDep,
) -> ClaimStatsResponse:
    by_status = await claim_service.get_claim_stats(current_user)
    return ClaimStatsResponse(total=sum(by_status.values()), by_status=by_status)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: ClaimIdPath,
    current_user: CurrentUserDep,
    claim_service: ClaimServiceDep,
) -> ClaimResponse:
    claim = await claim_service.get_claim(claim_id, current_user)
    return ClaimResponse.model_validate(claim)


@router.patch("/{claim_id}/status", response_model=ClaimResponse)
async def review_claim(
    claim_id: ClaimIdPath,
    request: ReviewClaimRequest,
    reviewer: ReviewerDep,
    claim_service: ClaimServiceDep,
) -> ClaimResponse:
    claim = await claim_service.review_claim(claim_id, request, reviewer)
    return ClaimResponse.model_validate(claim)
