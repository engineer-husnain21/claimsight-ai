"""Agent that writes the reviewer summary and suggested decision."""

from app.agents.base_agent import BaseAgent
from app.schemas.summary_input import SummaryInput
from app.schemas.summary_output import SummaryOutput


class SummaryAgent(BaseAgent[SummaryInput, SummaryOutput]):
    """Summarise extraction, validation and fraud results for a reviewer."""

    name = "summary"
    output_model = SummaryOutput

    async def run(self, agent_input: SummaryInput) -> SummaryOutput:
        """Return the summary, key points and recommended decision."""
        system_prompt = self._prompt_loader.load("summary_system")
        user_prompt = self._prompt_loader.render(
            "summary_user",
            claim_details=agent_input.extraction.model_dump_json(indent=2),
            validation_result=agent_input.validation.model_dump_json(indent=2),
            fraud_result=agent_input.fraud.model_dump_json(indent=2),
        )
        output = await self._generate_output(system_prompt, user_prompt)
        return self._never_approve_risky_claims(output, agent_input)

    @staticmethod
    def _never_approve_risky_claims(
        output: SummaryOutput, agent_input: SummaryInput
    ) -> SummaryOutput:
        """Downgrade an approval to review when checks found serious problems."""
        has_critical_issue = any(
            issue.severity == "critical" for issue in agent_input.validation.issues
        )
        is_risky = has_critical_issue or agent_input.fraud.risk_level != "low"
        if output.recommendation == "approved" and is_risky:
            return output.model_copy(update={"recommendation": "needs_review"})
        return output
