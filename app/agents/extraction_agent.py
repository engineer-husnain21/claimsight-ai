"""Agent that turns free-text claims into structured claim details."""

from app.agents.base_agent import BaseAgent
from app.schemas.extraction_input import ExtractionInput
from app.schemas.extraction_output import ExtractionOutput


class ExtractionAgent(BaseAgent[ExtractionInput, ExtractionOutput]):
    """Extract patient, treatment and billing facts from a claim."""

    name = "extraction"
    output_model = ExtractionOutput

    async def run(self, agent_input: ExtractionInput) -> ExtractionOutput:
        """Return the structured facts found in the claim text."""
        system_prompt = self._prompt_loader.load("extraction_system")
        user_prompt = self._prompt_loader.render(
            "extraction_user", claim_text=agent_input.claim_text
        )
        return await self._generate_output(system_prompt, user_prompt)
