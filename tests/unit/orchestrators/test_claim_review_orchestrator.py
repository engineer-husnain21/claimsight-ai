import json
from datetime import date

import pytest

from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.schemas.claim_review_input import ClaimReviewInput
from app.schemas.policy_chunk import PolicyChunk
from tests.fakes.routing_fake_llm_client import RoutingFakeLlmClient

EXTRACTION_REPLY = json.dumps(
    {"patient_name": "Ahmed Raza", "admission_type": "emergency", "total_amount": 1000}
)
VALIDATION_REPLY = json.dumps(
    {"is_compliant": True, "issues": [], "eligible_amount": 1000, "reasoning": "OK"}
)
FRAUD_REPLY = json.dumps({"risk_score": 5, "flags": [], "reasoning": "Clean"})
SUMMARY_REPLY = json.dumps(
    {"summary": "Clean claim.", "key_points": [], "recommendation": "approved"}
)


def _replies(**overrides: str) -> dict[str, str]:
    replies = {
        "extraction assistant": EXTRACTION_REPLY,
        "validation assistant": VALIDATION_REPLY,
        "fraud and anomaly": FRAUD_REPLY,
        "claims review assistant": SUMMARY_REPLY,
    }
    replies.update(overrides)
    return replies


def _chunk(rule_code: str) -> PolicyChunk:
    return PolicyChunk(
        id=f"policy:{rule_code}",
        source="policy",
        rule_code=rule_code,
        title=rule_code,
        text=f"{rule_code} rule text",
    )


def _orchestrator(llm_client: RoutingFakeLlmClient) -> ClaimReviewOrchestrator:
    prompt_loader = PromptLoader()
    return ClaimReviewOrchestrator(
        ExtractionAgent(llm_client, prompt_loader),
        ValidationAgent(llm_client, prompt_loader),
        FraudAgent(llm_client, prompt_loader),
        SummaryAgent(llm_client, prompt_loader),
    )


def _review_input() -> ClaimReviewInput:
    return ClaimReviewInput(
        claim_text="Ahmed Raza, emergency admission, PKR 1,000",
        validation_policy_chunks=[_chunk("COV-02")],
        fraud_policy_chunks=[_chunk("FRD-01")],
        review_date=date(2026, 10, 17),
    )


async def test_run_when_all_agents_succeed_returns_every_result() -> None:
    orchestrator = _orchestrator(RoutingFakeLlmClient(_replies()))

    result = await orchestrator.run(_review_input())

    assert result.extraction.patient_name == "Ahmed Raza"
    assert result.validation.is_compliant is True
    assert result.fraud.risk_level == "low"
    assert result.summary.recommendation == "approved"


async def test_run_when_all_agents_succeed_records_steps_in_flow_order() -> None:
    orchestrator = _orchestrator(RoutingFakeLlmClient(_replies()))

    result = await orchestrator.run(_review_input())

    agents = [step.agent for step in result.steps]
    assert agents[0] == "extraction"
    assert set(agents[1:3]) == {"validation", "fraud"}
    assert agents[3] == "summary"


async def test_run_when_called_sends_each_agent_only_its_own_rules() -> None:
    llm_client = RoutingFakeLlmClient(_replies())

    await _orchestrator(llm_client).run(_review_input())

    prompts = {call["key"]: call["user_prompt"] for call in llm_client.calls}
    assert "COV-02" in prompts["validation assistant"]
    assert "FRD-01" not in prompts["validation assistant"]
    assert "FRD-01" in prompts["fraud and anomaly"]
    assert "COV-02" not in prompts["fraud and anomaly"]


async def test_run_when_extraction_fails_stops_before_other_agents() -> None:
    llm_client = RoutingFakeLlmClient(_replies(**{"extraction assistant": "not json"}))

    with pytest.raises(LlmClientError):
        await _orchestrator(llm_client).run(_review_input())

    assert [call["key"] for call in llm_client.calls] == ["extraction assistant"]
