# Daily GitHub coding agent

This repository runs one short Python code-generation cycle in GitHub Actions at five configured UTC times each day. Each successful cycle creates a new file under `daily-code/`, validates it, commits it, and pushes it. The workflow does not run a server or container.

## Architecture

- `agent/agent.py` coordinates one cycle, selects the next number, adds a UTC timestamp, validates, and commits.
- `agent/llm.py` calls an OpenAI-compatible chat-completions API using environment variables.
- `agent/generator.py` supplies the four-line prompt, removes Markdown fences, and syntax-checks candidates.
- `agent/git_manager.py` stages only the generated file, commits, and retries a rejected push after fetch and rebase.
- `.github/workflows/daily-agent.yml` checks out the repository, installs Python 3.12, and runs the agent.

## Configure an LLM provider

Choose a provider that offers a free tier and an OpenAI-compatible chat completions endpoint. The free-tier terms and availability depend on the provider. Set these values in the repository:

- Repository **Settings → Secrets and variables → Actions → Secrets**: `LLM_API_KEY` (the provider API key).
- Repository **Settings → Secrets and variables → Actions → Variables**: `LLM_API_URL` (the full chat completions endpoint URL) and `LLM_MODEL` (the provider's model identifier).

No API key belongs in source code. The agent never prints the key. The GitHub Actions checkout token is supplied automatically by GitHub; no GitHub token secret is needed. `contents: write` grants the workflow permission to push.

## Schedule

GitHub requires literal cron expressions in `on.schedule`; it does not resolve repository variables there. To change execution times, edit the five cron entries in `.github/workflows/daily-agent.yml`. They use UTC and are currently 00:00, 04:00, 08:00, 12:00, and 16:00 UTC. Keep exactly five entries to retain five scheduled starts per day. GitHub cron scheduling can be delayed, and GitHub may disable schedules in inactive repositories, so this is five configured runs rather than a guarantee of exact wall-clock start times.

## Enable and run

Push this workflow to the repository's default branch and enable GitHub Actions for the repository. A scheduled run happens at each cron time. To test or start a cycle manually, open **Actions → Daily coding agent → Run workflow** (`workflow_dispatch`). Manual runs are additional and are not part of the five daily scheduled slots.

## Test locally

Use Python 3.12 and Git. Install declared dependencies with `python -m pip install -r requirements.txt` (the implementation uses only the standard library). In a disposable clone with a configured remote, provide the mock response to avoid any API call:

```powershell
$env:LLM_MOCK_RESPONSE = "value = 1 + 1"
python -B agent/agent.py
```

The mock runs a full cycle, including a local commit and push. To test Markdown fence extraction and syntax validation without committing, run:

```powershell
python -c "from agent.generator import extract_code, is_valid_python; source=extract_code('```python\nvalue = 1 + 1\n```'); assert is_valid_python(source); print(source, end='')"
```

## Cycle numbering and safeguards

Before each cycle, the agent scans `daily-code/cycle_*.py`, parses existing numeric suffixes, and chooses the next integer (formatted with at least three digits). Thus `cycle_999.py` is followed by `cycle_1000.py`; existing files are never overwritten. It makes up to three LLM/validation attempts. API or syntax failures create no commit. Code fences are removed, a UTC timestamp comment is prepended, and Python compilation runs in a temporary directory. Git stages only the new `daily-code/` file. If push is rejected, it fetches, rebases, and retries; a rebase conflict aborts safely. The workflow concurrency group prevents overlapping agent runs.

The generator prompt asks for harmless, self-contained code and prohibits filesystem, network, environment, credential, and repository-configuration access. As with any generated source code, review repository changes through normal Git history.
