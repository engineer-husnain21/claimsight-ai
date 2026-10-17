"""Agent that checks extracted claim details against policy rules."""

from app.agents.base_agent import BaseAgent
from app.schemas.validation_input import ValidationInput
from app.schemas.validation_output import ValidationOutput


class ValidationAgent(BaseAgent[ValidationInput, ValidationOutput]):
    """Check a claim against retrieved policy rules and report issues."""

    name = "validation"
    output_model = ValidationOutput

    async def run(self, agent_input: ValidationInput) -> ValidationOutput:
        """Return policy issues and the eligible amount for the claim."""
        policy_rules = "\n\n".join(
            f"[{chunk.rule_code}] {chunk.text}" for chunk in agent_input.policy_chunks
        )
        system_prompt = self._prompt_loader.load("validation_system")
        user_prompt = self._prompt_loader.render(
            "validation_user",
            policy_rules=policy_rules,
            claim_details=agent_input.extraction.model_dump_json(indent=2),
        )
        output = await self._generate_output(system_prompt, user_prompt)
        return self._keep_known_rule_codes(output, agent_input)

    @staticmethod
    def _keep_known_rule_codes(
        output: ValidationOutput, agent_input: ValidationInput
    ) -> ValidationOutput:
        """Drop issues that cite rules the agent was not given (hallucinations)."""
        known_codes = {chunk.rule_code for chunk in agent_input.policy_chunks}
        issues = [issue for issue in output.issues if issue.rule_code in known_codes]
        return output.model_copy(update={"issues": issues})
