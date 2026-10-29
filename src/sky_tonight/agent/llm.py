"""Chat model selection from config: LLM_MODEL="provider:model"."""

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

DEFAULT_MODEL = "openai:gpt-6-luna"

# Provider prefix -> (API key env var, optional extra that installs its LangChain package).
PROVIDERS = {"openai": ("OPENAI_API_KEY", "openai")}


class LLMConfigError(RuntimeError):
    pass


def model_name() -> str:
    return os.environ.get("LLM_MODEL") or DEFAULT_MODEL


def load_llm() -> BaseChatModel:
    name = model_name()
    provider = name.split(":", 1)[0] if ":" in name else None
    if provider not in PROVIDERS:
        supported = ", ".join(f"{p}:<model>" for p in PROVIDERS)
        raise LLMConfigError(f"Unsupported LLM_MODEL {name!r}. Supported: {supported}")

    key_var, extra = PROVIDERS[provider]
    if not os.environ.get(key_var):
        raise LLMConfigError(f"{key_var} is not set. Add it to your .env (see .env.example).")
    try:
        return init_chat_model(name)
    except ImportError as exc:
        raise LLMConfigError(
            f"The {provider} provider is not installed. Run: uv sync --extra {extra}"
        ) from exc
