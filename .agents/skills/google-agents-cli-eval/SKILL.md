---
name: google-agents-cli-eval
description: >-
  Use this skill when running evaluations, comparing mobile vs static agent
  performance, or analyzing ML model metrics. Covers the evaluation module,
  ML reports, and the comparison tab in the Streamlit UI.
---

# Eval — Evaluation & Comparison

Skill for evaluating and comparing agent performance.

## When to Use
- Running static vs mobile agent comparisons
- Generating ML classification reports
- Analyzing scenario outcomes (S01–S06)
- Working with `hotel_demo/evaluation.py` or `hotel_demo/ml.py`

## Steps

### 1. Run Evaluation via UI
1. Start the app: `python -m streamlit run app.py`
2. Open the **Evaluasi** tab.
3. Click **Jalankan Perbandingan**.
4. Review: business outcomes (identical for static/mobile), simulation costs (bytes, steps, ms).

### 2. Generate ML Report via CLI
```bash
# Output to JSON
python -m hotel_demo.ml --out ml_report.json

# Regenerate synthetic dataset
python -m hotel_demo.ml --regenerate
```

### 3. Key Metrics
| Metric | Description |
|--------|-------------|
| `p(human_judgment)` | ML probability that case needs human intervention |
| `threshold` | 0.80 — demo parameter |
| `decision_source` | `POLICY_MANDATORY` or `ML_PREDICTION` |
| Payload bytes | Canonical JSON size (not wire bytes) |
| Steps | Number of simulation steps |
| Latency (ms) | Compute time (not network benchmark) |

### 4. Test Evaluation
```bash
python -m pytest tests/test_evaluation.py -v
python -m pytest tests/test_ml.py -v
```

### 5. Important Notes
- ML uses logistic regression on 48 synthetic combinations — not a production model.
- Threshold 0.80 is a demo parameter, not optimized.
- Policy mandatory overrides ML prediction.
