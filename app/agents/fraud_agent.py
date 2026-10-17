"""Agent that scores a claim for fraud and anomaly risk."""

import json

from app.agents.base_agent import BaseAgent
from app.schemas.fraud_input import FraudInput
from app.schemas.fraud_output import FraudOutput


class FraudAgent(BaseAgent[FraudInput, FraudOutput]):
    """Find fraud indicators on a claim and give it a risk score."""

    name = "fraud"
    output_model = FraudOutput

    async def run(self, agent_input: FraudInput) -> FraudOutput:
        """Return the fraud risk score and the indicators behind it."""
        fraud_rules = "\n\n".join(
            f"[{chunk.rule_code}] {chunk.text}" for chunk in agent_input.policy_chunks
        )
        prior_claims = json.dumps(
            [claim.model_dump(mode="json") for claim in agent_input.prior_claims],
            indent=2,
        )
        system_prompt = self._prompt_loader.load("fraud_system")
        user_prompt = self._prompt_loader.render(
            "fraud_user",
            review_date=agent_input.review_date.isoformat(),
            fraud_rules=fraud_rules,
            prior_claims=prior_claims,
            claim_details=agent_input.extraction.model_dump_json(indent=2),
        )
        output = await self._generate_output(system_prompt, user_prompt)
        return self._keep_known_rule_codes(output, agent_input)

    @staticmethod
    def _keep_known_rule_codes(output: FraudOutput, agent_input: FraudInput) -> FraudOutput:
        """Drop flags that cite rules the agent was not given (hallucinations)."""
        known_codes = {chunk.rule_code for chunk in agent_input.policy_chunks}
        flags = [flag for flag in output.flags if flag.rule_code in known_codes]
        return output.model_copy(update={"flags": flags})
