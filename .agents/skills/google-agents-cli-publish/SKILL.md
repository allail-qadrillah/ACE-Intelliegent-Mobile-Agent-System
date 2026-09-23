---
name: google-agents-cli-publish
description: >-
  Use this skill when preparing the project for submission or presentation.
  Covers generating reports, exporting artifacts, formatting README, and
  creating a presentation-ready demo. Note: do NOT push to GitHub.
---

# Publish — Submission & Presentation

Skill for preparing the project for academic submission or live demo.

## When to Use
- Preparing files for course submission
- Creating demo scripts for presentation
- Generating ML reports and exported logs
- Formatting documentation

## Steps

### 1. Generate Artifacts
```bash
# ML classification report
python -m hotel_demo.ml --out ml_report.json

# Run all tests and capture output
python -m pytest -q > test_results.txt 2>&1
```

### 2. Verify Everything Works
```bash
# All tests pass
python -m pytest -q

# No dependency conflicts
pip check

# App starts without errors
python -m streamlit run app.py
```

### 3. Demo Script (Presentation)
Follow the step-by-step in README Section 3:
1. Launch app offline → select **Mobile Agent** mode + **S01**.
2. Show guest messages, `p(human_judgment)`, `threshold`, `decision_source`.
3. Step through until candidates R102/R103 obtained.
4. Show PREPARE → DEPART → ARRIVE migration steps.
5. Approve room change as guest → show reservation update.
6. Switch to **S02** → show `WAITING_HUMAN`.
7. Open **Evaluasi** tab → run comparison.

### 4. Submission Checklist
- [ ] All 65+ tests pass
- [ ] README.md is up to date
- [ ] IMPLEMENTATION_NOTES.md reflects current state
- [ ] `ml_report.json` generated
- [ ] No `.venv/` or `__pycache__/` in submission
- [ ] Commit message: `"final submission — Kelompok 5"`

### 5. IMPORTANT
- **Do NOT `git push`** — submit via local file transfer or university portal.
- Keep all data synthetic — no real hotel data.
