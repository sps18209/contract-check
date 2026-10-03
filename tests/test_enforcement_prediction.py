import unittest

from contract_check.enforcement.prediction.evaluate import metrics
from contract_check.enforcement.prediction.outcomes import validate_dataset
from contract_check.enforcement.prediction.train import run_experiment


class PredictionResearchTests(unittest.TestCase):
    def test_disabled_even_with_input(self):
        with self.assertRaisesRegex(ValueError, "disabled"):
            run_experiment({"schema": 1, "records": []})

    def test_metrics_and_no_training_on_tiny_dataset(self):
        self.assertAlmostEqual(metrics([0, 1], [0.2, 0.8])["brier"], 0.04)
        dataset = {"schema": 1, "event_definition": {"event": "fictional ruling", "population": "fictional", "forum": "fictional", "posture": "fictional", "horizon_days": 365}, "records": []}
        with self.assertRaisesRegex(ValueError, "insufficient"):
            run_experiment(dataset, enabled=True)

    def test_censored_or_leaky_label_rejected(self):
        dataset = {"schema": 1, "event_definition": {"event": "ruling", "population": "cases", "forum": "court", "posture": "motion", "horizon_days": 365},
                   "records": [{"matter_id": "one", "outcome": None, "jurisdiction": "MO", "issue_type": "remedy",
                                "snapshot_at": "2026-01-01", "resolved_at": "2026-02-01", "label_source": "record",
                                "population": "cases", "forum": "court", "posture": "motion", "disposition": "adjudicated",
                                "label_quote": "resolved", "features": {"jurisdiction": "MO", "issue_type": "remedy", "posture": "motion"}}]}
        with self.assertRaisesRegex(ValueError, "adjudicated"):
            validate_dataset(dataset)

    def test_offline_temporal_experiment_reports_aggregate_only(self):
        try:
            import sklearn  # noqa: F401 - optional dependency
        except ImportError:
            self.skipTest("optional prediction dependency unavailable")
        records = []
        for i in range(100):
            snap, resolved = (("2024-01-01", "2024-01-20") if i < 60 else
                              ("2024-02-01", "2024-02-20") if i < 80 else
                              ("2024-03-01", "2024-03-20"))
            records.append({"matter_id": f"fictional-{i}", "outcome": i % 2,
                            "jurisdiction": "MO", "issue_type": "condition", "snapshot_at": snap,
                            "population": "fictional cases", "forum": "fictional court", "posture": "motion", "disposition": "adjudicated",
                            "resolved_at": resolved, "label_source": "fictional fixture", "label_quote": "fictional result",
                            "features": {"jurisdiction": "MO", "issue_type": "condition", "contract_type": "services" if i % 2 else "sale", "posture": "motion"}})
        dataset = {"schema": 1, "event_definition": {"event": "fictional motion granted", "population": "fictional cases", "forum": "fictional court", "posture": "motion", "horizon_days": 365}, "records": records}
        result = run_experiment(dataset, enabled=True)
        self.assertEqual(result["partition_counts"], {"train": 60, "calibration": 20, "test": 20})
        self.assertEqual(result["test_metrics"]["n"], 20)
        self.assertIn("prevalence_baseline_brier", result)
        self.assertEqual(result["test_group_counts"], {"MO | condition": 20})
        self.assertNotIn("probabilities", result)

    def test_late_outcome_and_cohort_mismatch_rejected(self):
        base = {"schema": 1, "event_definition": {"event": "motion granted", "population": "filed motions", "forum": "state court", "posture": "motion", "horizon_days": 30},
                "records": [{"matter_id": "x", "outcome": 1, "disposition": "adjudicated", "population": "filed motions", "forum": "state court", "posture": "motion",
                             "jurisdiction": "MO", "issue_type": "condition", "snapshot_at": "2026-01-01", "resolved_at": "2026-03-01",
                             "label_source": "fixture", "label_quote": "granted", "features": {"jurisdiction": "MO", "issue_type": "condition", "posture": "motion"}}]}
        with self.assertRaisesRegex(ValueError, "horizon"):
            validate_dataset(base)
        base["records"][0]["resolved_at"] = "2026-01-15"
        base["records"][0]["forum"] = "federal court"
        with self.assertRaisesRegex(ValueError, "cohort"):
            validate_dataset(base)


if __name__ == "__main__":
    unittest.main()
