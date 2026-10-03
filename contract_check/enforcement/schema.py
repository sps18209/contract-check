"""Versioned interchange contracts for the optional enforcement module."""

from __future__ import annotations

from typing import Any
import hashlib
import json

from ..core import validate

SCHEMA = 1
ISSUE_TYPES = {"formation", "interpretation", "performance", "condition", "defense", "remedy", "collection", "other"}
FACT_STATES = {"established", "disputed", "inferred", "unknown"}
STATUSES = {"review_pending", "insufficient_information", "out_of_scope"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


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
    findings = {f["id"]: f for f in review["findings"]}
    seen = set()
    for q in request["questions"]:
        if not isinstance(q, dict) or not _nonempty(q.get("id")) or q["id"] in seen:
            raise ValueError("question needs a unique id")
        seen.add(q["id"])
        if q.get("finding_id") not in findings or q.get("issue_type") not in ISSUE_TYPES:
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
        finding_blocks = set(findings[q["finding_id"]]["affected_blocks"]) | {e["block_id"] for e in findings[q["finding_id"]]["evidence"]}
        if not any(row["block_id"] in finding_blocks for row in evidence):
            raise ValueError("question evidence does not connect to its finding")
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


def validate_assessment(project: dict, review: dict, request: dict, result: dict, manifest: dict | None = None) -> dict:
    from .abstention import missing_inputs
    from .authorities import resolve_authorities
    from .dependencies import map_dependencies
    from .facts import fact_summary
    from .provenance import verified_contract_evidence

    validate_request(project, review, request)
    manifest = manifest if manifest is not None else {"schema": 1, "authorities": []}
    if result.get("schema") != SCHEMA or result.get("source_sha256") != project["source_sha256"] or result.get("project_version") != project["version"]:
        raise ValueError("stale or invalid assessment")
    if result.get("request_sha256") != fingerprint(request) or result.get("manifest_sha256") != fingerprint(manifest):
        raise ValueError("assessment inputs changed")
    items = result.get("assessments")
    if not isinstance(items, list) or [i.get("question_id") for i in items] != [q["id"] for q in request["questions"]]:
        raise ValueError("assessment questions do not match request")
    for item, q in zip(items, request["questions"]):
        if item.get("status") not in STATUSES or not isinstance(item.get("reasons"), list) or not isinstance(item.get("missing"), list):
            raise ValueError("invalid assessment status or reasons")
        if item.get("outcome_probability") is not None:
            raise ValueError("outcome probability is not supported")
        if not isinstance(item.get("authority_ids"), list) or not isinstance(item.get("contract_evidence"), list):
            raise ValueError("assessment lacks provenance")
        authorities = resolve_authorities(q, manifest)
        missing = missing_inputs(q, authorities)
        if item.get("finding_id") != q["finding_id"] or item.get("issue_type") != q["issue_type"] or item["contract_evidence"] != verified_contract_evidence(project, q["evidence"]):
            raise ValueError("assessment evidence or scope changed")
        if item["authority_ids"] != [a["id"] for a in authorities] or item["missing"] != missing or item["status"] != ("insufficient_information" if missing else "review_pending"):
            raise ValueError("assessment gates or authorities changed")
        if item.get("authorities") != authorities or item.get("facts") != fact_summary(q) or item.get("dependencies") != map_dependencies(project, q):
            raise ValueError("assessment supporting records changed")
        if item.get("lawyer_review") != "pending":
            raise ValueError("lawyer review cannot be asserted by this module")
    return {"valid": True, "assessment_count": len(items)}
