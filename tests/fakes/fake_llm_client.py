"""Fake LLM client used by unit tests instead of a real provider."""


class FakeLlmClient:
    """LLM client for tests that returns a fixed reply and records calls."""

    def __init__(self, reply: str = "{}") -> None:
        self.reply = reply
        self.calls: list[dict[str, object]] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "json_mode": json_mode,
            }
        )
        return self.reply
