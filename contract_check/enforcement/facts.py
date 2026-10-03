"""Preserve the difference between source facts, disputes, and inference."""


def fact_summary(question: dict) -> dict:
    grouped = {state: [] for state in ("established", "disputed", "inferred", "unknown")}
    for fact in question["facts"]:
        grouped[fact["state"]].append({"statement": fact["statement"], "source": fact["source"]})
    return grouped
