"""Shared state passed between nodes of the claim review graph."""

import operator
from typing import Annotated, TypedDict

from app.schemas.agent_step import AgentStep
from app.schemas.claim_review_input import ClaimReviewInput
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_output import FraudOutput
from app.schemas.summary_output import SummaryOutput
from app.schemas.validation_output import ValidationOutput


class ClaimReviewState(TypedDict, total=False):
    """Graph state. Each node fills in its own key.

    `steps` uses `operator.add` so parallel nodes can both append to it.
    """

    request: ClaimReviewInput
    extraction: ExtractionOutput
    validation: ValidationOutput
    fraud: FraudOutput
    summary: SummaryOutput
    steps: Annotated[list[AgentStep], operator.add]
