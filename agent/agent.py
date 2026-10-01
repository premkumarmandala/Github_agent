"""Run one autonomous code generation cycle."""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import MAX_ATTEMPTS, OUTPUT_DIR, ROOT
from generator import PROMPT, extract_code, is_valid_python
from git_manager import commit_and_push
from llm import generate_code


def next_cycle(directory: Path) -> int:
    numbers = [
        int(match.group(1))
        for path in directory.glob("cycle_*.py")
        if (match := re.fullmatch(r"cycle_(\d+)\.py", path.name))
    ]
    return max(numbers, default=0) + 1


def run() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cycle = next_cycle(OUTPUT_DIR)
    target = OUTPUT_DIR / f"cycle_{cycle:03d}.py"
    if target.exists():
        print("Refusing to overwrite an existing cycle file.", file=sys.stderr)
        return 1

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            code = extract_code(generate_code(PROMPT))
        except (RuntimeError, ValueError) as exc:
            print(f"Generation attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}", file=sys.stderr)
            continue

        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        contents = f"# Generated at {timestamp}\n{code}"
        if not is_valid_python(contents):
            print(f"Generated code failed syntax validation on attempt {attempt}/{MAX_ATTEMPTS}.", file=sys.stderr)
            continue

        # The only created/modified repository path is under daily-code/.
        target.write_text(contents, encoding="utf-8")
        try:
            commit_and_push(ROOT, target.relative_to(ROOT), cycle)
        except RuntimeError as exc:
            target.unlink(missing_ok=True)
            print(f"Git operation failed: {exc}", file=sys.stderr)
            return 1
        print(f"Completed cycle {cycle}.")
        return 0

    print("No commit created because generation or validation failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
