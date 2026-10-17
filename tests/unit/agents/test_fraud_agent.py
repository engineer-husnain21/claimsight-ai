import json
from datetime import date

import pytest

from app.agents.fraud_agent import FraudAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_input import FraudInput, PriorClaim
from app.schemas.fraud_output import FraudOutput
from app.schemas.policy_chunk import PolicyChunk
from tests.fakes.fake_llm_client import FakeLlmClient


def _fraud_input() -> FraudInput:
    return FraudInput(
        extraction=ExtractionOutput(patient_name="Ahmed Raza", total_amount=253000),
        policy_chunks=[
            PolicyChunk(
                id="fraud_indicators:FRD-01",
                source="fraud_indicators",
                rule_code="FRD-01",
                title="Duplicate Claims",
                text="FRD-01 Duplicate Claims\nSame claim twice is fraud.",
            )
        ],
        prior_claims=[PriorClaim(claim_id="claim-7", total_amount=253000)],
        review_date=date(2026, 10, 17),
    )


def _reply(score: int, flags: list[dict[str, str]]) -> str:
    return json.dumps({"risk_score": score, "flags": flags, "reasoning": "Looks like a duplicate."})


async def test_run_when_llm_returns_valid_json_returns_fraud_result() -> None:
    flag = {"rule_code": "FRD-01", "message": "Same amount as claim-7"}
    agent = FraudAgent(FakeLlmClient(reply=_reply(80, [flag])), PromptLoader())

    result = await agent.run(_fraud_input())

    assert result.risk_score == 80
    assert result.risk_level == "high"
    assert [item.rule_code for item in result.flags] == ["FRD-01"]


async def test_run_when_called_puts_date_history_and_claim_in_user_prompt() -> None:
    llm_client = FakeLlmClient(reply=_reply(10, []))
    agent = FraudAgent(llm_client, PromptLoader())

    await agent.run(_fraud_input())

    user_prompt = str(llm_client.calls[0]["user_prompt"])
    assert "2026-10-17" in user_prompt
    assert "claim-7" in user_prompt
    assert "Ahmed Raza" in user_prompt


async def test_run_when_flag_cites_unknown_rule_drops_that_flag() -> None:
    flags = [
        {"rule_code": "FRD-01", "message": "Duplicate"},
        {"rule_code": "FRD-99", "message": "Made up rule"},
    ]
    agent = FraudAgent(FakeLlmClient(reply=_reply(75, flags)), PromptLoader())

    result = await agent.run(_fraud_input())

    assert [item.rule_code for item in result.flags] == ["FRD-01"]


async def test_run_when_risk_score_out_of_range_raises_error() -> None:
    agent = FraudAgent(FakeLlmClient(reply=_reply(150, [])), PromptLoader())

    with pytest.raises(LlmClientError):
        await agent.run(_fraud_input())


@pytest.mark.parametrize(
    ("score", "expected_level"), [(0, "low"), (29, "low"), (30, "medium"), (70, "high")]
)
def test_risk_level_when_score_given_returns_matching_bucket(
    score: int, expected_level: str
) -> None:
    output = FraudOutput(risk_score=score, reasoning="test")

    assert output.risk_level == expected_level
