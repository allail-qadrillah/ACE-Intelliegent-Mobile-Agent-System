---
name: google-agents-cli-adk-code
description: >-
  Use this skill when developing, modifying, or debugging agent code in the
  hotel_demo package. Covers creating new agents, editing agent logic in
  agents.py, modifying the migration protocol, and working with the pure
  evaluation kernel.
---

# ADK Code — Agent Development

Skill for writing and maintaining the core agent code in `hotel_demo/`.

## When to Use
- Creating a new agent type (e.g., a new specialist agent)
- Modifying existing agent behavior in `agents.py`
- Changing the migration protocol in `migration.py`
- Updating models/contracts in `models.py`
- Editing policy logic in `policy.py`

## Steps

### 1. Understand the Architecture
- All agents live in `hotel_demo/agents.py`.
- The `MobileInvestigator` agent uses `migration.py` for state transfer.
- Shared evaluation kernel: `evaluate_candidates()` — used by both mobile and static agents.
- Two logical nodes: `FRONT_OFFICE` and `OPERATIONS`.

### 2. Creating a New Agent
1. Define the agent class in `hotel_demo/agents.py`.
2. Give it a clear role and capabilities via configuration (not hardcoded).
3. Register it in the simulation engine (`simulation.py`).
4. Add tests in `tests/test_scenarios.py` or a new `tests/test_<agent>.py`.

### 3. Modifying Migration
1. Edit `hotel_demo/migration.py`.
2. Maintain invariants: zero-or-one owner, no shared reference, replay is no-op.
3. Run `python -m pytest tests/test_migration.py -v` to verify.

### 4. Validation
```bash
python -m pytest -q
```
All 65+ tests must pass before committing.
