"""LangGraph flow that runs the claim review agents in order."""

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.orchestrators.claim_review_state import ClaimReviewState
from app.schemas.agent_step import AgentStep
from app.schemas.claim_review_input import ClaimReviewInput
from app.schemas.claim_review_output import ClaimReviewOutput
from app.schemas.extraction_input import ExtractionInput
from app.schemas.fraud_input import FraudInput
from app.schemas.summary_input import SummaryInput
from app.schemas.validation_input import ValidationInput


class ClaimReviewOrchestrator:
    """Run extraction, then validation and fraud in parallel, then summary."""

    def __init__(
        self,
        extraction_agent: ExtractionAgent,
        validation_agent: ValidationAgent,
        fraud_agent: FraudAgent,
        summary_agent: SummaryAgent,
    ) -> None:
        self._extraction_agent = extraction_agent
        self._validation_agent = validation_agent
        self._fraud_agent = fraud_agent
        self._summary_agent = summary_agent
        self._graph = self._build_graph()

    async def run(self, review_input: ClaimReviewInput) -> ClaimReviewOutput:
        """Run the full agent flow for one claim and return every result."""
        state = await self._graph.ainvoke({"request": review_input, "steps": []})
        return ClaimReviewOutput(
            extraction=state["extraction"],
            validation=state["validation"],
            fraud=state["fraud"],
            summary=state["summary"],
            steps=state["steps"],
        )

    def _build_graph(self) -> Any:
        graph = StateGraph(ClaimReviewState)
        graph.add_node("extraction", self._extract)
        graph.add_node("validation", self._validate)
        graph.add_node("fraud", self._check_fraud)
        graph.add_node("summary", self._summarise)

        graph.add_edge(START, "extraction")
        graph.add_edge("extraction", "validation")
        graph.add_edge("extraction", "fraud")
        graph.add_edge(["validation", "fraud"], "summary")
        graph.add_edge("summary", END)
        return graph.compile()

    async def _extract(self, state: ClaimReviewState) -> ClaimReviewState:
        started = time.perf_counter()
        extraction = await self._extraction_agent.run(
            ExtractionInput(claim_text=state["request"].claim_text)
        )
        return {"extraction": extraction, "steps": [_step("extraction", started)]}

    async def _validate(self, state: ClaimReviewState) -> ClaimReviewState:
        started = time.perf_counter()
        validation = await self._validation_agent.run(
            ValidationInput(
                extraction=state["extraction"],
                policy_chunks=state["request"].validation_policy_chunks,
            )
        )
        return {"validation": validation, "steps": [_step("validation", started)]}

    async def _check_fraud(self, state: ClaimReviewState) -> ClaimReviewState:
        started = time.perf_counter()
        request = state["request"]
        fraud = await self._fraud_agent.run(
            FraudInput(
                extraction=state["extraction"],
                policy_chunks=request.fraud_policy_chunks,
                prior_claims=request.prior_claims,
                review_date=request.review_date,
            )
        )
        return {"fraud": fraud, "steps": [_step("fraud", started)]}

    async def _summarise(self, state: ClaimReviewState) -> ClaimReviewState:
        started = time.perf_counter()
        summary = await self._summary_agent.run(
            SummaryInput(
                extraction=state["extraction"],
                validation=state["validation"],
                fraud=state["fraud"],
            )
        )
        return {"summary": summary, "steps": [_step("summary", started)]}


def _step(agent: str, started: float) -> AgentStep:
    """Build a step record from a perf_counter start time."""
    return AgentStep(agent=agent, duration_ms=int((time.perf_counter() - started) * 1000))
