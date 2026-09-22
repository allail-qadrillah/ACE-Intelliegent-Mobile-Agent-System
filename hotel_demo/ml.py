"""ML lokal: dataset sintetis, training, prediksi, dan report.

Model memprediksi kebutuhan keputusan manusia (``needs_human_judgment``).
Dataset adalah 48 kombinasi kartesian dengan aturan anotasi sintetis untuk demo
belajar, bukan SOP hotel yang tervalidasi.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .models import sha256_hex

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATASET_PATH = DATA_DIR / "escalation_synthetic.csv"

FEATURE_ORDER = [
    "intent_complexity",
    "risk_level",
    "prior_failed_attempts",
    "context_missing",
]
CSV_COLUMNS = ["row_id"] + FEATURE_ORDER + ["needs_human_judgment"]
THRESHOLD = 0.80
MODEL_CODE_VERSION = "ml-v1"

DATASET_NOTE = (
    "Dataset sintetis 48 kombinasi; metrik hanya ilustrasi pada 12 contoh uji. "
    "Bukan validasi operasional hotel."
)
LABEL_RULE = (
    "score = intent_complexity + 2*risk_level + prior_failed_attempts + 2*context_missing; "
    "needs_human_judgment = int(score >= 6)"
)


def generate_rows() -> List[Dict[str, int]]:
    """48 baris unik dengan nested loop sesuai urutan kolom fitur."""
    rows: List[Dict[str, int]] = []
    index = 1
    for intent_complexity in (1, 2, 3, 4):
        for risk_level in (0, 1):
            for prior_failed_attempts in (0, 1, 2):
                for context_missing in (0, 1):
                    score = (
                        intent_complexity
                        + 2 * risk_level
                        + prior_failed_attempts
                        + 2 * context_missing
                    )
                    rows.append(
                        {
                            "row_id": f"E{index:03d}",
                            "intent_complexity": intent_complexity,
                            "risk_level": risk_level,
                            "prior_failed_attempts": prior_failed_attempts,
                            "context_missing": context_missing,
                            "needs_human_judgment": int(score >= 6),
                        }
                    )
                    index += 1
    return rows


def rows_to_csv(rows: Sequence[Dict[str, Any]]) -> str:
    lines = [",".join(CSV_COLUMNS)]
    for row in rows:
        lines.append(",".join(str(row[column]) for column in CSV_COLUMNS))
    return "\n".join(lines) + "\n"


def write_dataset(path: Optional[Path] = None) -> Path:
    target = Path(path) if path else DATASET_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rows_to_csv(generate_rows()), encoding="utf-8")
    return target


def load_rows(path: Optional[Path] = None) -> List[Dict[str, int]]:
    target = Path(path) if path else DATASET_PATH
    if not target.exists():
        write_dataset(target)
    text = target.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    header = lines[0].split(",")
    rows: List[Dict[str, Any]] = []
    for line in lines[1:]:
        values = line.split(",")
        rows.append(
            {
                key: (value if key == "row_id" else int(value))
                for key, value in zip(header, values)
            }
        )
    return rows


def dataset_sha256(rows: Optional[Sequence[Dict[str, Any]]] = None) -> str:
    data = rows if rows is not None else load_rows()
    return sha256_hex(rows_to_csv(data).encode("utf-8"))


def features_vector(features: Dict[str, Any]) -> List[float]:
    return [float(features[name]) for name in FEATURE_ORDER]


class MLModel:
    """Wrapper read-only pipeline + report yang benar-benar dihitung."""

    def __init__(self, pipeline: Any, report: Dict[str, Any]) -> None:
        self.pipeline = pipeline
        self.report = report

    def predict(self, features: Dict[str, Any]) -> float:
        vector = [features_vector(features)]
        probabilities = self.pipeline.predict_proba(vector)[0]
        classes = list(self.pipeline.classes_)
        positive_index = classes.index(1)
        return float(probabilities[positive_index])

    @property
    def dataset_sha256(self) -> str:
        return self.report["dataset"]["sha256"]

    def describe(self) -> Dict[str, Any]:
        return self.report


def train(csv_path: Optional[Path] = None) -> MLModel:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rows = load_rows(csv_path)
    if len(rows) != 48:
        raise ValueError(f"Dataset harus berisi 48 baris, ditemukan {len(rows)}.")

    X = [[row[name] for name in FEATURE_ORDER] for row in rows]
    y = [row["needs_human_judgment"] for row in rows]
    row_ids = [row["row_id"] for row in rows]

    X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
        X, y, row_ids, test_size=0.25, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(C=1.0, max_iter=1000, random_state=42)),
        ]
    )
    pipeline.fit(X_train, y_train)

    probabilities = [
        float(proba[list(pipeline.classes_).index(1)])
        for proba in pipeline.predict_proba(X_test)
    ]
    predictions = [1 if p >= THRESHOLD else 0 for p in probabilities]

    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    report: Dict[str, Any] = {
        "model": {
            "type": "Pipeline(StandardScaler, LogisticRegression)",
            "C": 1.0,
            "max_iter": 1000,
            "random_state": 42,
            "code_version": MODEL_CODE_VERSION,
        },
        "dataset": {
            "n_total": len(rows),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "sha256": dataset_sha256(rows),
            "feature_order": list(FEATURE_ORDER),
            "label_rule": LABEL_RULE,
            "note": DATASET_NOTE,
        },
        "threshold": THRESHOLD,
        "metrics": {
            "n_test": len(y_test),
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(
                precision_score(y_test, predictions, zero_division=0)
            ),
            "recall": float(recall_score(y_test, predictions, zero_division=0)),
            "f1": float(f1_score(y_test, predictions, zero_division=0)),
            "confusion_matrix": {
                "labels": [0, 1],
                "matrix": [[int(v) for v in row] for row in matrix],
                "tn": int(matrix[0][0]),
                "fp": int(matrix[0][1]),
                "fn": int(matrix[1][0]),
                "tp": int(matrix[1][1]),
            },
        },
        "manifest": {
            "train_row_ids": list(ids_train),
            "test_row_ids": list(ids_test),
        },
        "test_predictions": [
            {
                "row_id": row_id,
                "y_true": int(y_true),
                "p_human": round(p, 6),
                "y_pred": int(y_pred),
            }
            for row_id, y_true, p, y_pred in zip(ids_test, y_test, probabilities, predictions)
        ],
    }
    return MLModel(pipeline, report)


def load_or_train(csv_path: Optional[Path] = None) -> MLModel:
    return train(csv_path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Latih dan laporkan model ML lokal (tanpa jaringan)."
    )
    parser.add_argument("--dataset", type=str, default=str(DATASET_PATH))
    parser.add_argument("--regenerate", action="store_true", help="Tulis ulang dataset CSV.")
    parser.add_argument("--out", type=str, default=None, help="Tulis report JSON ke path ini.")
    args = parser.parse_args(argv)

    if args.regenerate:
        path = write_dataset(Path(args.dataset))
        print(f"Dataset ditulis ulang: {path}")

    model = train(Path(args.dataset))
    report = model.describe()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report ditulis: {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
