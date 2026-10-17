"""Combined result of all agents for one claim."""

from pydantic import BaseModel

from app.schemas.agent_step import AgentStep
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_output import FraudOutput
from app.schemas.summary_output import SummaryOutput
from app.schemas.validation_output import ValidationOutput


class ClaimReviewOutput(BaseModel):
    """Outputs of every agent plus the order and timing of their runs."""

    extraction: ExtractionOutput
    validation: ValidationOutput
    fraud: FraudOutput
    summary: SummaryOutput
    steps: list[AgentStep]
