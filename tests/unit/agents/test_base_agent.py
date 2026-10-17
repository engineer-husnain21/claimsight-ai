from pathlib import Path

import pytest
from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.core.exceptions import LlmClientError
from app.core.prompt_loader import PromptLoader
from tests.fakes.fake_llm_client import FakeLlmClient


class EchoInput(BaseModel):
    text: str


class EchoOutput(BaseModel):
    answer: str


class EchoAgent(BaseAgent[EchoInput, EchoOutput]):
    name = "echo"
    output_model = EchoOutput

    async def run(self, agent_input: EchoInput) -> EchoOutput:
        system_prompt = self._prompt_loader.load("echo_system")
        user_prompt = self._prompt_loader.render("echo_user", text=agent_input.text)
        return await self._generate_output(system_prompt, user_prompt)


@pytest.fixture
def fake_llm_client() -> FakeLlmClient:
    return FakeLlmClient()


@pytest.fixture
def prompt_loader(tmp_path: Path) -> PromptLoader:
    (tmp_path / "echo_system.md").write_text("Reply in JSON.", encoding="utf-8")
    (tmp_path / "echo_user.md").write_text("Text: $text", encoding="utf-8")
    return PromptLoader(tmp_path)


async def test_run_when_llm_returns_valid_json_returns_output(
    fake_llm_client: FakeLlmClient, prompt_loader: PromptLoader
) -> None:
    fake_llm_client.reply = '{"answer": "hello"}'
    agent = EchoAgent(fake_llm_client, prompt_loader)

    result = await agent.run(EchoInput(text="hi"))

    assert result == EchoOutput(answer="hello")
    assert fake_llm_client.calls[0]["user_prompt"] == "Text: hi"
    assert fake_llm_client.calls[0]["json_mode"] is True


async def test_run_when_llm_returns_invalid_json_raises_error(
    fake_llm_client: FakeLlmClient, prompt_loader: PromptLoader
) -> None:
    fake_llm_client.reply = "not json"
    agent = EchoAgent(fake_llm_client, prompt_loader)

    with pytest.raises(LlmClientError):
        await agent.run(EchoInput(text="hi"))
