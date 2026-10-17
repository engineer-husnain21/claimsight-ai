"""Base class shared by all AI agents."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.clients.llm_client import LlmClient
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class BaseAgent(ABC, Generic[TInput, TOutput]):
    """Common setup for agents: one LLM client, one prompt loader, one job."""

    name: str
    output_model: type[TOutput]

    def __init__(self, llm_client: LlmClient, prompt_loader: PromptLoader) -> None:
        self._llm_client = llm_client
        self._prompt_loader = prompt_loader

    @abstractmethod
    async def run(self, agent_input: TInput) -> TOutput:
        """Run the agent's single task and return its output."""

    async def _generate_output(self, system_prompt: str, user_prompt: str) -> TOutput:
        """Call the LLM in JSON mode and validate the reply as the output model."""
        raw_output = await self._llm_client.generate(system_prompt, user_prompt, json_mode=True)
        try:
            return self.output_model.model_validate_json(raw_output)
        except ValidationError as exc:
            raise LlmClientError("The language model returned invalid output.") from exc
