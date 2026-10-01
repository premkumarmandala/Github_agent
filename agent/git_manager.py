"""Git operations limited to adding the generated daily-code file."""

import subprocess
from pathlib import Path


def _run(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode:
        # Never echo Git stderr: remote errors can include credential-bearing URLs.
        raise RuntimeError(f"Git command failed ({args[1] if len(args) > 1 else args[0]})")
    return result


def commit_and_push(root: Path, relative_file: Path, cycle: int) -> None:
    _run(["git", "config", "user.name", "Daily Code Agent"], root)
    _run(["git", "config", "user.email", "actions@github.com"], root)
    _run(["git", "add", "--", relative_file.as_posix()], root)
    staged = _run(["git", "diff", "--cached", "--name-only"], root)
    staged_paths = {line.strip() for line in staged.stdout.splitlines() if line.strip()}
    if staged_paths != {relative_file.as_posix()}:
        raise RuntimeError("Refusing to commit: staged paths are outside the generated file")
    _run(["git", "commit", "-m", f"chore: daily code cycle {cycle}"], root)

    push = _run(["git", "push"], root, check=False)
    if push.returncode == 0:
        return

    # Rebase our single local commit on the fetched remote tip, then retry once.
    fetch = _run(["git", "fetch", "origin"], root, check=False)
    if fetch.returncode:
        raise RuntimeError("Git fetch failed after push rejection")
    branch = _run(["git", "branch", "--show-current"], root).stdout.strip()
    if not branch:
        raise RuntimeError("Cannot safely rebase from a detached HEAD")
    rebase = _run(["git", "rebase", f"origin/{branch}"], root, check=False)
    if rebase.returncode:
        _run(["git", "rebase", "--abort"], root, check=False)
        raise RuntimeError("Git rebase failed; local changes were not pushed")
    retry = _run(["git", "push"], root, check=False)
    if retry.returncode:
        raise RuntimeError("Git push retry failed")
