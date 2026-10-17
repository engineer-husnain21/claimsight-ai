"""Fake LLM client that picks its reply based on the system prompt."""


class RoutingFakeLlmClient:
    """Return the reply whose key appears in the system prompt.

    Lets one fake serve several agents in the same flow.
    """

    def __init__(self, replies: dict[str, str]) -> None:
        self.replies = replies
        self.calls: list[dict[str, str]] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_mode: bool = False,
    ) -> str:
        for key, reply in self.replies.items():
            if key in system_prompt:
                self.calls.append({"key": key, "user_prompt": user_prompt})
                return reply
        raise AssertionError("No fake reply configured for this system prompt.")
