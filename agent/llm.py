"""Small OpenAI-compatible chat completions client using the standard library."""

import json
import os
import urllib.error
import urllib.request

from config import API_TIMEOUT_SECONDS, llm_settings


def generate_code(prompt: str) -> str:
    """Request text from a compatible chat-completions endpoint.

    LLM_MOCK_RESPONSE is an opt-in local testing hook; it makes no network call.
    """
    mock = os.environ.get("LLM_MOCK_RESPONSE")
    if mock is not None:
        return mock

    api_key, api_url, model = llm_settings()
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        # Do not include request headers or exception details that might contain secrets.
        raise RuntimeError(f"LLM request failed ({type(exc).__name__})") from None
