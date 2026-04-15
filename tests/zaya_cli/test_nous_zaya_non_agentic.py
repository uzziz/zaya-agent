"""Tests for the Nous-Zaya-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"zaya"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``zaya-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "zaya" tag namespace.

``is_nous_zaya_non_agentic`` should only match the actual Nous Research
Zaya-3 / Zaya-4 chat family.
"""

from __future__ import annotations

import pytest

from zaya_cli.model_switch import (
    _ZAYA_MODEL_WARNING,
    _check_zaya_model_warning,
    is_nous_zaya_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "NousResearch/Zaya-3-Llama-3.1-70B",
        "NousResearch/Zaya-3-Llama-3.1-405B",
        "zaya-3",
        "Zaya-3",
        "zaya-4",
        "zaya-4-405b",
        "zaya_4_70b",
        "openrouter/zaya3:70b",
        "openrouter/nousresearch/zaya-4-405b",
        "NousResearch/Zaya3",
        "zaya-3.1",
    ],
)
def test_matches_real_nous_zaya_chat_models(model_name: str) -> None:
    assert is_nous_zaya_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Nous Zaya 3/4"
    )
    assert _check_zaya_model_warning(model_name) == _ZAYA_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "zaya-brain:qwen3-14b-ctx16k",
        "zaya-brain:qwen3-14b-ctx32k",
        "zaya-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Zaya models we don't warn about
        "zaya-llm-2",
        "zaya2-pro",
        "nous-zaya-2-mistral",
        # Edge cases
        "",
        "zaya",  # bare "zaya" isn't the 3/4 family
        "zaya-brain",
        "brain-zaya-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_nous_zaya_non_agentic(model_name), (
        f"expected {model_name!r} NOT to be flagged as Nous Zaya 3/4"
    )
    assert _check_zaya_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_nous_zaya_non_agentic("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_zaya_model_warning("") == ""
