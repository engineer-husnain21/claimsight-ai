import json

import pytest

from app.agents.summary_agent import SummaryAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_output import FraudOutput
from app.schemas.summary_input import SummaryInput
from app.schemas.validation_output import PolicyIssue, ValidationOutput
from tests.fakes.fake_llm_client import FakeLlmClient


def _summary_input(risk_score: int = 10, issues: list[PolicyIssue] | None = None) -> SummaryInput:
    return SummaryInput(
        extraction=ExtractionOutput(patient_name="Ahmed Raza", total_amount=253000),
        validation=ValidationOutput(
            is_compliant=not issues,
            issues=issues or [],
            eligible_amount=239500,
            reasoning="Room excess removed.",
        ),
        fraud=FraudOutput(risk_score=risk_score, reasoning="No concerns."),
    )


def _reply(recommendation: str) -> str:
    return json.dumps(
        {
            "summary": "Appendectomy claim, eligible PKR 239,500.",
            "key_points": ["Check COV-02 room excess"],
            "recommendation": recommendation,
        }
    )


async def test_run_when_llm_returns_valid_json_returns_summary() -> None:
    agent = SummaryAgent(FakeLlmClient(reply=_reply("approved")), PromptLoader())

    result = await agent.run(_summary_input())

    assert result.recommendation == "approved"
    assert result.key_points == ["Check COV-02 room excess"]


async def test_run_when_called_puts_all_results_in_user_prompt() -> None:
    llm_client = FakeLlmClient(reply=_reply("needs_review"))
    agent = SummaryAgent(llm_client, PromptLoader())

    await agent.run(_summary_input())

    user_prompt = str(llm_client.calls[0]["user_prompt"])
    assert "Ahmed Raza" in user_prompt
    assert "239500" in user_prompt
    assert "No concerns." in user_prompt


async def test_run_when_fraud_risk_not_low_downgrades_approval() -> None:
    agent = SummaryAgent(FakeLlmClient(reply=_reply("approved")), PromptLoader())

    result = await agent.run(_summary_input(risk_score=45))

    assert result.recommendation == "needs_review"


async def test_run_when_critical_issue_downgrades_approval() -> None:
    issue = PolicyIssue(rule_code="EXC-01", severity="critical", message="Cosmetic")
    agent = SummaryAgent(FakeLlmClient(reply=_reply("approved")), PromptLoader())

    result = await agent.run(_summary_input(issues=[issue]))

    assert result.recommendation == "needs_review"


async def test_run_when_recommendation_invalid_raises_error() -> None:
    agent = SummaryAgent(FakeLlmClient(reply=_reply("maybe")), PromptLoader())

    with pytest.raises(LlmClientError):
        await agent.run(_summary_input())
