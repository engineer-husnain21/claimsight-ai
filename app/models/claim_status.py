from enum import StrEnum


class ClaimStatus(StrEnum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
