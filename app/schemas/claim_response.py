from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.claim_status import ClaimStatus


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_number: str
    patient_name: str
    policy_number: str
    hospital_name: str
    diagnosis: str
    procedure: str
    amount_claimed: int
    status: ClaimStatus
    risk_score: float | None
    ai_summary: str | None
    submitted_by: str
    created_at: datetime
    updated_at: datetime
