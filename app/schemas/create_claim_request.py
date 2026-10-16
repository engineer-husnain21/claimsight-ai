from pydantic import BaseModel, ConfigDict, Field


class CreateClaimRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_name: str = Field(min_length=2, max_length=255)
    policy_number: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9-]+$")
    hospital_name: str = Field(min_length=2, max_length=255)
    diagnosis: str = Field(min_length=2, max_length=2000)
    procedure: str = Field(min_length=2, max_length=255)
    amount_claimed: int = Field(gt=0, le=100_000_000)
