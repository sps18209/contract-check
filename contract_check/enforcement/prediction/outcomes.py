"""Outcome cohort contract. Settlements and unresolved matters are not negatives."""

from datetime import date, timedelta

MIN_TRAIN = 60
MIN_CALIBRATION = 20
MIN_TEST = 20


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("dates must use YYYY-MM-DD") from None


def validate_dataset(dataset: dict) -> list[dict]:
    if not isinstance(dataset, dict) or dataset.get("schema") != 1:
        raise ValueError("invalid outcome dataset")
    definition = dataset.get("event_definition")
    if not isinstance(definition, dict) or any(not isinstance(definition.get(k), str) or not definition[k].strip() for k in ("event", "population", "forum", "posture")) or type(definition.get("horizon_days")) is not int or definition["horizon_days"] <= 0:
        raise ValueError("define event, population, forum, posture, and positive horizon_days")
    records = dataset.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    ids = set()
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("matter_id"), str) or not row["matter_id"] or row["matter_id"] in ids:
            raise ValueError("unique matter_id required")
        ids.add(row["matter_id"])
        if row.get("outcome") not in (0, 1) or type(row["outcome"]) is not int:
            raise ValueError("outcome must be adjudicated 0 or 1; exclude censored cases")
        if row.get("disposition") != "adjudicated":
            raise ValueError("exclude unresolved, settled, or censored cases")
        if any(row.get(k) != definition[k] for k in ("population", "forum", "posture")):
            raise ValueError("record lies outside the defined cohort")
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ("jurisdiction", "issue_type", "snapshot_at", "resolved_at", "label_source", "label_quote")):
            raise ValueError("record lacks feature or label provenance")
        if _date(row["resolved_at"]) < _date(row["snapshot_at"]):
            raise ValueError("resolution cannot precede feature snapshot")
        if _date(row["resolved_at"]) > _date(row["snapshot_at"]) + timedelta(days=definition["horizon_days"]):
            raise ValueError("resolution lies beyond the defined horizon; exclude as censored")
        if not isinstance(row.get("features"), dict) or any(k not in ("contract_type", "issue_type", "jurisdiction", "posture") or not isinstance(v, str) for k, v in row["features"].items()):
            raise ValueError("features must be from the approved pre-outcome schema")
        if row["features"].get("issue_type") != row["issue_type"] or row["features"].get("jurisdiction") != row["jurisdiction"]:
            raise ValueError("feature and cohort metadata disagree")
        if row["features"].get("posture") != row["posture"]:
            raise ValueError("posture feature and cohort metadata disagree")
    return records
