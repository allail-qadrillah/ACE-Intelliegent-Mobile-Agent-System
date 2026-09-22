"""AC-21 dan AC-22: dataset, split, training, dan interaksi ML dengan skenario."""

from __future__ import annotations

import numpy as np
import pytest

from hotel_demo import ml
from hotel_demo.simulation import load_scenarios

LOW_RISK_SCENARIOS = ("S01", "S04", "S05", "S06")


def test_dataset_file_matches_generator():
    rows = ml.generate_rows()
    assert len(rows) == 48
    assert ml.rows_to_csv(rows) == ml.DATASET_PATH.read_text(encoding="utf-8")
    assert ml.dataset_sha256(rows) == ml.dataset_sha256()


def test_dataset_rows_are_unique_and_follow_label_rule():
    rows = ml.generate_rows()
    combos = {
        (
            row["intent_complexity"],
            row["risk_level"],
            row["prior_failed_attempts"],
            row["context_missing"],
        )
        for row in rows
    }
    assert len(combos) == 48
    assert [row["row_id"] for row in rows] == [f"E{index:03d}" for index in range(1, 49)]
    for row in rows:
        score = (
            row["intent_complexity"]
            + 2 * row["risk_level"]
            + row["prior_failed_attempts"]
            + 2 * row["context_missing"]
        )
        assert row["needs_human_judgment"] == int(score >= 6)


def test_split_is_36_12_without_overlap(model):
    report = model.report
    assert report["dataset"]["n_total"] == 48
    assert report["dataset"]["n_train"] == 36
    assert report["dataset"]["n_test"] == 12
    train_ids = set(report["manifest"]["train_row_ids"])
    test_ids = set(report["manifest"]["test_row_ids"])
    assert train_ids.isdisjoint(test_ids)
    assert len(train_ids | test_ids) == 48


def test_scaler_fit_on_train_only(model):
    rows = {row["row_id"]: row for row in ml.load_rows()}
    train_ids = model.report["manifest"]["train_row_ids"]
    expected_mean = np.mean(
        [[rows[row_id][name] for name in ml.FEATURE_ORDER] for row_id in train_ids], axis=0
    )
    scaler = model.pipeline.named_steps["scaler"]
    assert np.allclose(scaler.mean_, expected_mean)


def test_report_uses_threshold_and_real_probabilities(model):
    report = model.report
    assert report["threshold"] == pytest.approx(0.80)
    assert report["metrics"]["n_test"] == 12
    for metric in ("accuracy", "precision", "recall", "f1"):
        assert 0.0 <= report["metrics"][metric] <= 1.0
    matrix = report["metrics"]["confusion_matrix"]["matrix"]
    assert len(matrix) == 2 and len(matrix[0]) == 2
    for prediction in report["test_predictions"]:
        assert 0.0 <= prediction["p_human"] <= 1.0
        assert prediction["y_pred"] == int(prediction["p_human"] >= 0.80)


def test_predictions_are_model_output_not_hardcoded(model):
    low = model.predict(
        {"intent_complexity": 2, "risk_level": 0, "prior_failed_attempts": 0, "context_missing": 0}
    )
    high = model.predict(
        {"intent_complexity": 4, "risk_level": 1, "prior_failed_attempts": 2, "context_missing": 1}
    )
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0
    assert high > low
    assert low != pytest.approx(0.961, abs=1e-6)


def test_low_risk_scenarios_below_threshold(model):
    scenarios = load_scenarios()
    for scenario_id in LOW_RISK_SCENARIOS:
        probability = model.predict(scenarios[scenario_id]["features"])
        assert probability < 0.80, f"{scenario_id} p={probability}"
