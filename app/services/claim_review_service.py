"""Run the AI agents on a claim and keep the result for reviewers."""

from app.core.clock import utc_now
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models.claim import Claim
from app.models.claim_review import ClaimReview
from app.models.user import User
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.claim_review_repository import ClaimReviewRepository
from app.schemas.claim_review_input import ClaimReviewInput
from app.schemas.fraud_input import PriorClaim
from app.services.claim_service import PRIVILEGED_ROLES
from app.services.policy_retrieval_service import PolicyRetrievalService

MAX_PRIOR_CLAIMS = 20
_CLAIM_NOT_FOUND = "Claim not found."


class ClaimReviewService:
    """Business rules for AI reviews: who may run them, what goes in, what is saved."""

    def __init__(
        self,
        claim_repository: ClaimRepository,
        claim_review_repository: ClaimReviewRepository,
        audit_log_repository: AuditLogRepository,
        policy_retrieval_service: PolicyRetrievalService,
        orchestrator: ClaimReviewOrchestrator,
        llm_model: str,
    ) -> None:
        self._claim_repository = claim_repository
        self._claim_review_repository = claim_review_repository
        self._audit_log_repository = audit_log_repository
        self._policy_retrieval_service = policy_retrieval_service
        self._orchestrator = orchestrator
        self._llm_model = llm_model

    async def run_review(self, claim_id: str, reviewer: User) -> ClaimReview:
        """Run every agent on the claim, save the review and update the claim."""
        claim = await self._get_reviewable_claim(claim_id, reviewer)
        if claim.submitted_by == reviewer.id:
            raise ForbiddenError("You cannot review your own claim.")

        policies = await self._policy_retrieval_service.retrieve_for_claim(
            claim.diagnosis, claim.procedure
        )
        if not policies.validation_chunks or not policies.fraud_chunks:
            raise AppError("Policy rules are not loaded. Run the policy ingestion script.")

        result = await self._orchestrator.run(
            ClaimReviewInput(
                claim_text=_build_claim_text(claim),
                validation_policy_chunks=policies.validation_chunks,
                fraud_policy_chunks=policies.fraud_chunks,
                prior_claims=await self._load_prior_claims(claim),
                review_date=utc_now().date(),
            )
        )

        review = await self._claim_review_repository.add(
            ClaimReview(
                claim_id=claim.id,
                requested_by=reviewer.id,
                recommendation=result.summary.recommendation,
                risk_score=float(result.fraud.risk_score),
                eligible_amount=result.validation.eligible_amount,
                llm_model=self._llm_model,
                result=result.model_dump(mode="json"),
            )
        )
        claim.risk_score = float(result.fraud.risk_score)
        claim.ai_summary = result.summary.summary
        await self._claim_repository.save(claim)
        await self._audit_log_repository.record(
            user_id=reviewer.id,
            action="claim.ai_reviewed",
            resource_type="claim",
            resource_id=claim.id,
            details={
                "claim_number": claim.claim_number,
                "review_id": review.id,
                "recommendation": review.recommendation,
                "risk_score": review.risk_score,
            },
        )
        return review

    async def get_latest_review(self, claim_id: str, user: User) -> ClaimReview:
        """Return the newest AI review of a claim."""
        claim = await self._get_reviewable_claim(claim_id, user)
        review = await self._claim_review_repository.get_latest_for_claim(claim.id)
        if review is None:
            raise NotFoundError("This claim has no AI review yet.")
        return review

    async def _get_reviewable_claim(self, claim_id: str, user: User) -> Claim:
        # Submitters never see AI reviews, so risk scores cannot be gamed.
        if user.role not in PRIVILEGED_ROLES:
            raise ForbiddenError()
        claim = await self._claim_repository.get_by_id(claim_id)
        if claim is None:
            raise NotFoundError(_CLAIM_NOT_FOUND)
        return claim

    async def _load_prior_claims(self, claim: Claim) -> list[PriorClaim]:
        """Earlier claims from the same submitter, for duplicate and frequency checks."""
        claims, _ = await self._claim_repository.list_claims(
            submitter_id=claim.submitted_by,
            status=None,
            limit=MAX_PRIOR_CLAIMS + 1,
            offset=0,
        )
        return [
            PriorClaim(
                claim_id=other.claim_number,
                service_date=other.created_at.date(),
                total_amount=float(other.amount_claimed),
                diagnosis=other.diagnosis,
            )
            for other in claims
            if other.id != claim.id
        ][:MAX_PRIOR_CLAIMS]


def _build_claim_text(claim: Claim) -> str:
    """Turn the stored claim fields into the text the extraction agent reads."""
    return "\n".join(
        [
            f"Claim number: {claim.claim_number}",
            f"Patient: {claim.patient_name}",
            f"Policy number: {claim.policy_number}",
            f"Hospital: {claim.hospital_name}",
            f"Diagnosis: {claim.diagnosis}",
            f"Procedure: {claim.procedure}",
            f"Amount claimed: PKR {claim.amount_claimed:,}",
            f"Submitted on: {claim.created_at.date().isoformat()}",
        ]
    )
