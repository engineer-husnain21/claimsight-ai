import json

import pytest

from app.agents.validation_agent import ValidationAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.policy_chunk import PolicyChunk
from app.schemas.validation_input import ValidationInput
from tests.fakes.fake_llm_client import FakeLlmClient


def _validation_input() -> ValidationInput:
    return ValidationInput(
        extraction=ExtractionOutput(
            patient_name="Ahmed Raza",
            admission_type="emergency",
            total_amount=253000,
        ),
        policy_chunks=[
            PolicyChunk(
                id="exclusions_policy:EXC-05",
                source="exclusions_policy",
                rule_code="EXC-05",
                title="Non-medical Charges",
                text="EXC-05 Non-medical Charges\nFood is excluded.",
            )
        ],
    )


def _reply(issues: list[dict[str, str]]) -> str:
    return json.dumps(
        {
            "is_compliant": False,
            "issues": issues,
            "eligible_amount": 248500,
            "reasoning": "Attendant food is not covered.",
        }
    )


async def test_run_when_llm_returns_valid_json_returns_validation() -> None:
    issue = {"rule_code": "EXC-05", "severity": "warning", "message": "Food excluded"}
    agent = ValidationAgent(FakeLlmClient(reply=_reply([issue])), PromptLoader())

    result = await agent.run(_validation_input())

    assert result.is_compliant is False
    assert result.eligible_amount == 248500
    assert [item.rule_code for item in result.issues] == ["EXC-05"]


async def test_run_when_called_puts_rules_and_claim_in_user_prompt() -> None:
    llm_client = FakeLlmClient(reply=_reply([]))
    agent = ValidationAgent(llm_client, PromptLoader())

    await agent.run(_validation_input())

    user_prompt = str(llm_client.calls[0]["user_prompt"])
    assert "[EXC-05]" in user_prompt
    assert "Ahmed Raza" in user_prompt


async def test_run_when_issue_cites_unknown_rule_drops_that_issue() -> None:
    issues = [
        {"rule_code": "EXC-05", "severity": "warning", "message": "Food excluded"},
        {"rule_code": "XYZ-99", "severity": "critical", "message": "Made up rule"},
    ]
    agent = ValidationAgent(FakeLlmClient(reply=_reply(issues)), PromptLoader())

    result = await agent.run(_validation_input())

    assert [item.rule_code for item in result.issues] == ["EXC-05"]


async def test_run_when_severity_invalid_raises_error() -> None:
    issue = {"rule_code": "EXC-05", "severity": "urgent", "message": "Bad"}
    agent = ValidationAgent(FakeLlmClient(reply=_reply([issue])), PromptLoader())

    with pytest.raises(LlmClientError):
        await agent.run(_validation_input())
