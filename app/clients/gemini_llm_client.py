"""Gemini implementation of the LlmClient protocol."""

import httpx
from google import genai
from google.genai import errors, types

from app.core.exceptions import LlmClientError


class GeminiLlmClient:
    """LLM client that calls the Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self._model = model
        self._temperature = temperature

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        """Send the prompts to Gemini and return the response text."""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self._temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=config,
            )
        except (errors.APIError, httpx.HTTPError) as exc:
            raise LlmClientError("The language model request failed.") from exc

        content = response.text
        if not content:
            raise LlmClientError("The language model returned an empty response.")
        return content
