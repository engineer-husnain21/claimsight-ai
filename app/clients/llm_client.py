"""LLM client protocol shared by all provider implementations."""

from typing import Protocol


class LlmClient(Protocol):
    """Interface for chat-completion style LLM clients."""

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text response for the given prompts.

        Args:
            system_prompt: Instructions that define the model's behaviour.
            user_prompt: The task or content for the model to process.
            json_mode: If True, ask the provider to return valid JSON only.

        Returns:
            The raw text content of the model's response.
        """
        ...
