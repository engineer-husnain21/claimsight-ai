"""Input for the summary agent."""

from pydantic import BaseModel

from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_output import FraudOutput
from app.schemas.validation_output import ValidationOutput


class SummaryInput(BaseModel):
    """Results of the earlier agents, to be summarised for a human reviewer."""

    extraction: ExtractionOutput
    validation: ValidationOutput
    fraud: FraudOutput
