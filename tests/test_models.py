import pytest

from agents.models import build_model


def test_plain_gemini_name_passes_through():
    assert build_model("gemini-3.5-flash-lite") == "gemini-3.5-flash-lite"
    assert build_model("models/gemini-3.5-flash-lite") == "models/gemini-3.5-flash-lite"


def test_provider_model_needs_litellm(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.endswith("lite_llm"):
            raise ImportError("no litellm")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="requirements-litellm"):
        build_model("openai/gpt-x")
