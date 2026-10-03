"""Versioned interchange contracts for the optional enforcement module."""

from __future__ import annotations

from typing import Any

from ..core import validate

SCHEMA = 1
ISSUE_TYPES = {"formation", "interpretation", "performance", "condition", "defense", "remedy", "collection", "other"}
FACT_STATES = {"established", "disputed", "inferred", "unknown"}
STATUSES = {"review_pending", "insufficient_information", "out_of_scope"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_request(project: dict, review: dict, request: dict) -> dict:
    from ..review import validate_review

    validate(project)
    validate_review(project, review)
    if not isinstance(request, dict) or request.get("schema") != SCHEMA:
        raise ValueError("invalid enforcement request schema")
    if request.get("source_sha256") != project["source_sha256"] or request.get("project_version") != project["version"]:
        raise ValueError("stale or unrelated enforcement request")
    if not isinstance(request.get("questions"), list):
        raise ValueError("questions must be a list")
    blocks = {b["id"]: b["text"] for b in project["blocks"]}
    finding_ids = {f["id"] for f in review["findings"]}
    seen = set()
    for q in request["questions"]:
        if not isinstance(q, dict) or not _nonempty(q.get("id")) or q["id"] in seen:
            raise ValueError("question needs a unique id")
        seen.add(q["id"])
        if q.get("finding_id") not in finding_ids or q.get("issue_type") not in ISSUE_TYPES:
            raise ValueError("question needs a review finding and valid issue type")
        for field in ("enforcing_party", "resisting_party", "asserted_duty", "requested_remedy", "governing_law", "forum", "posture", "event_date"):
            if not _nonempty(q.get(field)):
                raise ValueError(f"question missing {field}; use unknown explicitly")
        evidence = q.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("question needs contract evidence")
        for row in evidence:
            if not isinstance(row, dict) or row.get("block_id") not in blocks or not _nonempty(row.get("quote")) or row["quote"] not in blocks[row["block_id"]]:
                raise ValueError("question quote does not occur in cited block")
        if not isinstance(q.get("facts"), list):
            raise ValueError("facts must be a list")
        for fact in q["facts"]:
            if not isinstance(fact, dict) or not _nonempty(fact.get("statement")) or fact.get("state") not in FACT_STATES or not _nonempty(fact.get("source")):
                raise ValueError("fact needs statement, state, and source")
            if fact["state"] == "established" and fact["source"] in ("inference", "unknown"):
                raise ValueError("inference cannot be recorded as established")
        if not isinstance(q.get("authority_ids", []), list) or any(not _nonempty(x) for x in q.get("authority_ids", [])):
            raise ValueError("authority_ids must be strings")
    return {"valid": True, "question_count": len(seen)}


def validate_assessment(project: dict, review: dict, request: dict, result: dict) -> dict:
    validate_request(project, review, request)
    if result.get("schema") != SCHEMA or result.get("source_sha256") != project["source_sha256"] or result.get("project_version") != project["version"]:
        raise ValueError("stale or invalid assessment")
    items = result.get("assessments")
    if not isinstance(items, list) or [i.get("question_id") for i in items] != [q["id"] for q in request["questions"]]:
        raise ValueError("assessment questions do not match request")
    for item in items:
        if item.get("status") not in STATUSES or not isinstance(item.get("reasons"), list) or not isinstance(item.get("missing"), list):
            raise ValueError("invalid assessment status or reasons")
        if item.get("outcome_probability") is not None:
            raise ValueError("outcome probability is not supported")
        if not isinstance(item.get("authority_ids"), list) or not isinstance(item.get("contract_evidence"), list):
            raise ValueError("assessment lacks provenance")
    return {"valid": True, "assessment_count": len(items)}
