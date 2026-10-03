"""Explicitly opted-in, offline research experiment. Never called by assess()."""

from datetime import date

from .evaluate import metrics
from .outcomes import MIN_TRAIN, MIN_CALIBRATION, MIN_TEST, validate_dataset

FIELDS = ("contract_type", "issue_type", "jurisdiction", "posture")


def _feature(row):
    return {key: row["features"].get(key, "unknown") for key in FIELDS}


def _both_classes(rows):
    return {r["outcome"] for r in rows} == {0, 1}


def run_experiment(dataset: dict, *, enabled: bool = False) -> dict:
    if enabled is not True:
        raise ValueError("prediction experiment disabled; explicit opt-in required")
    rows = sorted(validate_dataset(dataset), key=lambda r: (r["snapshot_at"], r["matter_id"]))
    if len(rows) < MIN_TRAIN + MIN_CALIBRATION + MIN_TEST:
        raise ValueError("insufficient labeled matters for research experiment")
    n = len(rows)
    train_end, cal_end = int(n * 0.6), int(n * 0.8)
    train, cal, test = rows[:train_end], rows[train_end:cal_end], rows[cal_end:]
    if min(len(train) / MIN_TRAIN, len(cal) / MIN_CALIBRATION, len(test) / MIN_TEST) < 1:
        raise ValueError("insufficient sample in temporal partition")
    if train[-1]["snapshot_at"] == cal[0]["snapshot_at"] or cal[-1]["snapshot_at"] == test[0]["snapshot_at"]:
        raise ValueError("temporal partition splits the same snapshot date")
    if any(date.fromisoformat(r["resolved_at"]) >= date.fromisoformat(cal[0]["snapshot_at"]) for r in train):
        raise ValueError("training outcomes were not known before calibration snapshots")
    if any(date.fromisoformat(r["resolved_at"]) >= date.fromisoformat(test[0]["snapshot_at"]) for r in cal):
        raise ValueError("calibration outcomes were not known before test snapshots")
    if not all(_both_classes(part) for part in (train, cal, test)):
        raise ValueError("each partition needs positive and negative outcomes")
    try:
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError as exc:
        raise ValueError("install the optional prediction dependencies") from exc
    # Logistic baseline; separate sigmoid calibrator trained only on later labels.
    base = make_pipeline(DictVectorizer(), LogisticRegression(max_iter=1000))
    base.fit([_feature(r) for r in train], [r["outcome"] for r in train])
    scores = base.decision_function([_feature(r) for r in cal]).reshape(-1, 1)
    calibration = LogisticRegression(max_iter=1000)
    calibration.fit(scores, [r["outcome"] for r in cal])
    test_scores = base.decision_function([_feature(r) for r in test]).reshape(-1, 1)
    probabilities = calibration.predict_proba(test_scores)[:, 1].tolist()
    report = metrics([r["outcome"] for r in test], probabilities)
    prevalence = sum(r["outcome"] for r in train) / len(train)
    baseline = metrics([r["outcome"] for r in test], [prevalence] * len(test))
    def window(part):
        return {"first_snapshot": part[0]["snapshot_at"], "last_snapshot": part[-1]["snapshot_at"], "n": len(part)}
    groups = {}
    for row in test:
        key = row["jurisdiction"] + " | " + row["issue_type"]
        groups[key] = groups.get(key, 0) + 1
    return {"status": "research_only", "event_definition": dataset["event_definition"],
            "partition_counts": {"train": len(train), "calibration": len(cal), "test": len(test)},
            "partition_windows": {"train": window(train), "calibration": window(cal), "test": window(test)},
            "test_group_counts": groups, "train_prevalence": prevalence,
            "prevalence_baseline_brier": baseline["brier"], "test_metrics": report,
            "limitations": ["No deployment approval", "No individual contract prediction",
                "Audit selection bias, subgroup coverage, and label quality before interpreting results."]}
