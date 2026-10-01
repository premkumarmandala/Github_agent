"""Prompting, response cleanup, and syntax validation."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROMPT = """Generate approximately four lines of valid Python code.
Return code only, with no explanation. Keep it harmless and self-contained;
do not access the filesystem, network, environment variables, credentials, or
repository configuration. A short comment is acceptable."""


def extract_code(response: str) -> str:
    """Remove a surrounding Markdown fence while preserving actual code."""
    text = response.strip()
    match = re.search(r"```(?:python|py)?\s*\n(.*?)\n?```", text, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1).strip()
    if not text or text.startswith("```"):
        raise ValueError("LLM response did not contain extractable code")
    return text + "\n"


def is_valid_python(code: str) -> bool:
    """Compile source without leaving bytecode artifacts in the repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "candidate.py"
        source.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(source)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
