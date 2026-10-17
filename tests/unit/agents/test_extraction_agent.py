import json
from datetime import date

import pytest

from app.agents.extraction_agent import ExtractionAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from app.schemas.extraction_input import ExtractionInput
from tests.fakes.fake_llm_client import FakeLlmClient

VALID_REPLY = {
    "patient_name": "Ali Khan",
    "diagnosis": "Appendicitis",
    "procedures": ["Appendectomy"],
    "admission_type": "inpatient",
    "admission_date": "2026-10-01",
    "discharge_date": "2026-10-03",
    "line_items": [{"description": "Surgery", "amount": 120000}],
    "total_amount": 120000,
    "documents_provided": ["hospital bill", "discharge summary"],
    "has_preauthorization": None,
}


async def test_run_when_llm_returns_valid_json_returns_extraction() -> None:
    llm_client = FakeLlmClient(reply=json.dumps(VALID_REPLY))
    agent = ExtractionAgent(llm_client, PromptLoader())

    result = await agent.run(ExtractionInput(claim_text="Ali Khan, appendectomy"))

    assert result.patient_name == "Ali Khan"
    assert result.admission_type == "inpatient"
    assert result.admission_date == date(2026, 10, 1)
    assert result.line_items[0].amount == 120000


async def test_run_when_called_puts_claim_text_in_user_prompt() -> None:
    llm_client = FakeLlmClient(reply=json.dumps(VALID_REPLY))
    agent = ExtractionAgent(llm_client, PromptLoader())

    await agent.run(ExtractionInput(claim_text="MRI scan for knee pain"))

    assert "MRI scan for knee pain" in str(llm_client.calls[0]["user_prompt"])
    assert llm_client.calls[0]["json_mode"] is True


async def test_run_when_admission_type_invalid_raises_error() -> None:
    reply = {**VALID_REPLY, "admission_type": "holiday"}
    agent = ExtractionAgent(FakeLlmClient(reply=json.dumps(reply)), PromptLoader())

    with pytest.raises(LlmClientError):
        await agent.run(ExtractionInput(claim_text="some claim"))
