"""Configuration for the daily code agent."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "daily-code"
MAX_ATTEMPTS = 3
API_TIMEOUT_SECONDS = 45


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def llm_settings() -> tuple[str, str, str]:
    return (
        required_env("LLM_API_KEY"),
        required_env("LLM_API_URL"),
        required_env("LLM_MODEL"),
    )
