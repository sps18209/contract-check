"""Conservative scope and evidence gates; never synthesize a legal conclusion."""

from .schema import ISSUE_TYPES


def missing_inputs(question: dict, verified_authorities: list[dict]) -> list[str]:
    missing = []
    for field in ("governing_law", "forum", "posture", "event_date", "enforcing_party", "resisting_party", "asserted_duty", "requested_remedy"):
        if question[field].strip().lower() == "unknown":
            missing.append(field)
    if question["issue_type"] not in ISSUE_TYPES or question["issue_type"] == "other":
        missing.append("defined_legal_issue")
    if not question["facts"] or any(f["state"] == "unknown" for f in question["facts"]):
        missing.append("material_facts")
    if not any(a.get("reviewer_verified") is True for a in verified_authorities):
        missing.append("verified_authority")
    return missing
