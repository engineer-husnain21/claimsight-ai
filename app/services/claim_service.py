import uuid
from collections.abc import Sequence

from app.core.clock import utc_now
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.claim import Claim
from app.models.claim_status import ClaimStatus
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.review_claim_request import ReviewClaimRequest

CLAIM_NUMBER_PREFIX = "CLM"
PRIVILEGED_ROLES = {UserRole.ADMIN, UserRole.REVIEWER}
_NOT_FOUND = "Claim not found."


def _generate_claim_number() -> str:
    stamp = utc_now().strftime("%Y%m%d")
    return f"{CLAIM_NUMBER_PREFIX}-{stamp}-{uuid.uuid4().hex[:8].upper()}"


class ClaimService:
    """Business rules for creating, reading and reviewing claims."""

    def __init__(
        self,
        claim_repository: ClaimRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self._claim_repository = claim_repository
        self._audit_log_repository = audit_log_repository

    async def create_claim(self, request: CreateClaimRequest, user: User) -> Claim:
        claim = Claim(
            claim_number=_generate_claim_number(),
            patient_name=request.patient_name,
            policy_number=request.policy_number,
            hospital_name=request.hospital_name,
            diagnosis=request.diagnosis,
            procedure=request.procedure,
            amount_claimed=request.amount_claimed,
            status=ClaimStatus.SUBMITTED,
            submitted_by=user.id,
        )
        saved = await self._claim_repository.add(claim)
        await self._audit_log_repository.record(
            user_id=user.id,
            action="claim.created",
            resource_type="claim",
            resource_id=saved.id,
            details={"claim_number": saved.claim_number},
        )
        return saved

    async def get_claim(self, claim_id: str, user: User) -> Claim:
        claim = await self._claim_repository.get_by_id(claim_id)
        # Same error for "missing" and "not yours", so ids cannot be probed.
        if claim is None or not self._can_access(claim, user):
            raise NotFoundError(_NOT_FOUND)
        return claim

    async def list_claims(
        self,
        user: User,
        status: ClaimStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Claim], int]:
        submitter_id = None if user.role in PRIVILEGED_ROLES else user.id
        return await self._claim_repository.list_claims(
            submitter_id=submitter_id, status=status, limit=limit, offset=offset
        )

    async def review_claim(
        self, claim_id: str, request: ReviewClaimRequest, reviewer: User
    ) -> Claim:
        if reviewer.role not in PRIVILEGED_ROLES:
            raise ForbiddenError()

        claim = await self._claim_repository.get_by_id(claim_id)
        if claim is None:
            raise NotFoundError(_NOT_FOUND)
        if claim.submitted_by == reviewer.id:
            raise ForbiddenError("You cannot review your own claim.")

        previous_status = claim.status
        claim.status = request.status
        saved = await self._claim_repository.save(claim)
        await self._audit_log_repository.record(
            user_id=reviewer.id,
            action="claim.reviewed",
            resource_type="claim",
            resource_id=saved.id,
            details={
                "claim_number": saved.claim_number,
                "from": previous_status.value,
                "to": request.status.value,
                "note": request.note,
            },
        )
        return saved

    @staticmethod
    def _can_access(claim: Claim, user: User) -> bool:
        return user.role in PRIVILEGED_ROLES or claim.submitted_by == user.id
