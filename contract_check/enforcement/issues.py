"""Candidate issue mapping. Lexical cues are questions, never legal findings."""

import re

from ..review import validate_review
from .schema import SCHEMA

_CUES = {
    "formation": re.compile(r"\b(?:acceptance|offer|signature|consideration|execute[ds]?)\b", re.I),
    "interpretation": re.compile(r"\b(?:means|including|unless|except|sole discretion)\b", re.I),
    "performance": re.compile(r"\b(?:deliver|perform|pay|provide|complete)\b", re.I),
    "condition": re.compile(r"\b(?:condition precedent|subject to|provided that|upon receipt)\b", re.I),
    "defense": re.compile(r"\b(?:waiver|fraud|duress|unconscionab|impossib)\w*\b", re.I),
    "remedy": re.compile(r"\b(?:damages|injunction|specific performance|liquidated|terminate)\b", re.I),
    "collection": re.compile(r"\b(?:guaranty|security interest|collateral)\b", re.I),
}


def candidate_types(text: str) -> list[str]:
    """Suggest categories for human selection, without declaring legal validity."""
    return [kind for kind, pattern in _CUES.items() if pattern.search(text)]


def request_template(project: dict, review: dict) -> dict:
    validate_review(project, review)
    questions = []
    for finding in review["findings"]:
        if not finding["evidence"]:
            continue  # An absence finding needs the lawyer to identify the question's provision.
        quote = " ".join(row["quote"] for row in finding["evidence"])
        candidates = candidate_types(quote + " " + finding["issue"])
        questions.append({
            "id": "E-" + finding["id"], "finding_id": finding["id"],
            "issue_type": candidates[0] if candidates else "interpretation",
            "candidate_types": candidates,  # Remove after lawyer confirms the chosen type.
            "enforcing_party": "unknown", "resisting_party": "unknown",
            "asserted_duty": "unknown", "requested_remedy": "unknown",
            "governing_law": review["context"]["jurisdiction"], "forum": "unknown",
            "posture": "unknown", "event_date": "unknown",
            "evidence": finding["evidence"], "facts": [], "authority_ids": [],
        })
    return {"schema": SCHEMA, "source_sha256": project["source_sha256"],
            "project_version": project["version"], "questions": questions}
