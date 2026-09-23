# Working Rules

## Development Workflow
1. Always activate the virtual environment before working:
   ```bash
   source .venv/Scripts/activate
   ```
2. After making code changes, run tests immediately:
   ```bash
   python -m pytest -q
   ```
3. If tests pass, commit locally:
   ```bash
   git add -A && git commit -m "<descriptive message>"
   ```
4. Do NOT run `git push` — all work stays local.

## File Organization
- Entry point: `app.py`
- Core logic: `hotel_demo/` package
  - `models.py` — enums, dataclasses, Case, message/event contracts
  - `repository.py` — SQLite, guarded tools, atomic commits, idempotency
  - `policy.py` — mandatory policy + room change validation
  - `ml.py` — dataset, split, fit, predict, report
  - `agents.py` — static agents + MobileInvestigator + pure kernel
  - `migration.py` — prepare / depart / arrive / restore + invariant checks
  - `simulation.py` — engine, queue, event log, case lifecycle
  - `evaluation.py` — static vs mobile comparison
  - `ui.py` — Streamlit rendering
- Tests: `tests/`
- Data: `data/`
- Streamlit config: `.streamlit/config.toml`

## When Modifying Code
- Preserve all existing comments and docstrings unless explicitly asked to change them.
- When adding new agent types, register them in `agents.py` and add corresponding tests.
- When modifying the migration protocol, update `migration.py` and run `test_migration.py`.
- When changing policy rules, update `policy.py` and run `test_policy.py`.
- When modifying scenarios, update `data/scenarios.json` and `test_scenarios.py`.

## Running the Application
```bash
# Run the Streamlit app
python -m streamlit run app.py

# Generate ML report
python -m hotel_demo.ml --out ml_report.json

# Regenerate synthetic data
python -m hotel_demo.ml --regenerate
```
