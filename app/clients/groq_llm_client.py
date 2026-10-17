"""Groq implementation of the LlmClient protocol."""

from groq import APIError, AsyncGroq

from app.core.exceptions import LlmClientError


class GroqLlmClient:
    """LLM client that calls the Groq chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._client = AsyncGroq(api_key=api_key, timeout=timeout_seconds)
        self._model = model
        self._temperature = temperature

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        """Send the prompts to Groq and return the response text."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._temperature,
                response_format={"type": "json_object"} if json_mode else None,
            )
        except APIError as exc:
            raise LlmClientError("The language model request failed.") from exc

        content = response.choices[0].message.content
        if not content:
            raise LlmClientError("The language model returned an empty response.")
        return content
