"""Load prompt templates from markdown files in app/prompts."""

import re
from pathlib import Path
from string import Template

from app.core.exceptions import AppError

DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PROMPT_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


class PromptLoader:
    """Read prompt files once and render them with variables."""

    def __init__(self, prompts_dir: Path = DEFAULT_PROMPTS_DIR) -> None:
        self._prompts_dir = prompts_dir
        self._cache: dict[str, str] = {}

    def load(self, name: str) -> str:
        """Return the raw text of the prompt file `<name>.md`."""
        if not PROMPT_NAME_PATTERN.fullmatch(name):
            raise AppError("Invalid prompt name.")

        if name not in self._cache:
            path = self._prompts_dir / f"{name}.md"
            if not path.is_file():
                raise AppError("Prompt file not found.")
            self._cache[name] = path.read_text(encoding="utf-8")

        return self._cache[name]

    def render(self, name: str, **values: str) -> str:
        """Return the prompt with `$placeholders` replaced by the given values."""
        try:
            return Template(self.load(name)).substitute(values)
        except (KeyError, ValueError) as exc:
            raise AppError("Prompt rendering failed.") from exc
