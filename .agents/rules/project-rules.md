# Project Rules

## Architecture
- Single Python process with two logical nodes: `FRONT_OFFICE` and `OPERATIONS`.
- Two in-memory SQLite databases (one per node) + `applied_operations` for idempotency.
- Local queue via `collections.deque` — no threads, no background jobs.
- Agents: Scenario Scout, Orchestrator, Reservation, Billing, Concierge, Operations, Mobile Investigator.

## Code Conventions
- Language: Python 3.11+
- Use type hints everywhere (`from __future__ import annotations`).
- Docstrings: Google-style (triple double quotes).
- Formatting: follow PEP 8; max line length 100.
- All user-facing strings (UI labels, scenario descriptions) in **Bahasa Indonesia**.
- Code identifiers, comments explaining logic, and docstrings in **English**.

## Dependencies
- Only add packages listed in `requirements.txt`.
- Do NOT add deep-learning, LLM, or NLP libraries — the project uses logistic regression + rules.
- When adding new dependencies, ensure no version conflicts with existing ones.

## Testing
- Test framework: `pytest` (run `python -m pytest -q`).
- Test files live in `tests/` and are named `test_*.py`.
- All tests must pass offline — no network calls at test time.
- Cover: migration invariants, policy, repository transactions, scenarios, evaluation, and Streamlit smoke.

## Data
- All data is synthetic and local.
- Seed data: `data/hotel_seed.json`, `data/scenarios.json`, `data/escalation_synthetic.csv`.
- No API calls, no LLM calls, no credential usage at runtime.

## Git Policy
- Commit locally only — do NOT `git push` to any remote.
- Write meaningful commit messages in English.
- Keep `.venv/`, `__pycache__/`, `.pytest_cache/` out of commits (use `.gitignore`).

## Security & Limits
- SHA-256 is demo integrity check, NOT authentication.
- Allowlist/capability validation is simulated access control, not OS sandbox.
- ML threshold `0.80` is a demo parameter, not production-optimized.
