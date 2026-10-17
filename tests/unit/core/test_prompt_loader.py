from pathlib import Path

import pytest

from app.core.exceptions import AppError
from app.core.prompt_loader import PromptLoader


def test_load_when_file_exists_returns_text(tmp_path: Path) -> None:
    (tmp_path / "demo_system.md").write_text("You are a helper.", encoding="utf-8")
    loader = PromptLoader(tmp_path)
    assert loader.load("demo_system") == "You are a helper."


def test_load_when_file_missing_raises_error(tmp_path: Path) -> None:
    loader = PromptLoader(tmp_path)
    with pytest.raises(AppError):
        loader.load("missing_prompt")


def test_load_when_name_has_path_traversal_raises_error(tmp_path: Path) -> None:
    loader = PromptLoader(tmp_path)
    with pytest.raises(AppError):
        loader.load("../secrets")


def test_render_when_values_given_replaces_placeholders(tmp_path: Path) -> None:
    (tmp_path / "demo_user.md").write_text(
        'Claim: $claim_text\nReturn {"ok": true}', encoding="utf-8"
    )
    loader = PromptLoader(tmp_path)
    result = loader.render("demo_user", claim_text="X-ray, 5000 PKR")
    assert result == 'Claim: X-ray, 5000 PKR\nReturn {"ok": true}'


def test_render_when_value_missing_raises_error(tmp_path: Path) -> None:
    (tmp_path / "demo_user.md").write_text("Claim: $claim_text", encoding="utf-8")
    loader = PromptLoader(tmp_path)
    with pytest.raises(AppError):
        loader.render("demo_user")
