"""Structured claim details produced by the extraction agent."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

AdmissionType = Literal["inpatient", "outpatient", "emergency", "maternity", "unknown"]


class ClaimLineItem(BaseModel):
    """One billed item on the claim, amount in PKR."""

    description: str
    amount: float = Field(ge=0)


class ExtractionOutput(BaseModel):
    """Claim facts pulled out of free text. Missing facts stay null or empty."""

    patient_name: str | None = None
    diagnosis: str | None = None
    procedures: list[str] = Field(default_factory=list)
    admission_type: AdmissionType = "unknown"
    admission_date: date | None = None
    discharge_date: date | None = None
    line_items: list[ClaimLineItem] = Field(default_factory=list)
    total_amount: float | None = Field(default=None, ge=0)
    documents_provided: list[str] = Field(default_factory=list)
    has_preauthorization: bool | None = None
