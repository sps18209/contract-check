"""Research metrics; distinguish calibration from ranking and sample coverage."""


def metrics(labels: list[int], probabilities: list[float], bins: int = 10) -> dict:
    if len(labels) != len(probabilities) or not labels or bins < 2:
        raise ValueError("aligned nonempty labels and predictions required")
    if any(type(y) is not int or y not in (0, 1) for y in labels) or any(not isinstance(p, (float, int)) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("binary labels and probabilities in [0,1] required")
    n = len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / n
    partitions = [[] for _ in range(bins)]
    for y, p in zip(labels, probabilities):
        partitions[min(int(p * bins), bins - 1)].append((y, p))
    table = [{"count": len(part), "predicted_mean": sum(p for _, p in part) / len(part),
              "observed_rate": sum(y for y, _ in part) / len(part)}
             for part in partitions if part]
    ece = sum(row["count"] / n * abs(row["predicted_mean"] - row["observed_rate"]) for row in table)
    return {"n": n, "positive": sum(labels), "negative": n - sum(labels),
            "brier": brier, "ece_descriptive": ece, "calibration_bins": table}
