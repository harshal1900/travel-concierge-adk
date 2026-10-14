"""Model selection: plain names go to ADK's Gemini support, 'provider/model' goes through LiteLLM."""

from google.adk.models.base_llm import BaseLlm


def build_model(name: str) -> str | BaseLlm:
    if "/" not in name or name.startswith(("models/", "projects/", "publishers/")):
        return name
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:  # litellm is an optional dependency
        raise RuntimeError(
            f"LLM_MODEL={name!r} needs LiteLLM: pip install -r requirements-litellm.txt"
        ) from exc
    return LiteLlm(model=name)
