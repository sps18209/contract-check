"""Assemble reviewable issue records with conservative abstention."""

from .abstention import missing_inputs
from .authorities import resolve_authorities
from .dependencies import map_dependencies
from .facts import fact_summary
from .provenance import verified_contract_evidence
from .providers.rules import RulesProvider
from .schema import SCHEMA, fingerprint, validate_assessment, validate_request


def assess(project: dict, review: dict, request: dict, manifest: dict | None = None, provider=None) -> dict:
    validate_request(project, review, request)
    manifest = manifest if manifest is not None else {"schema": 1, "authorities": []}
    provider = provider if provider is not None else RulesProvider()
    items = []
    for q in request["questions"]:
        authorities = resolve_authorities(q, manifest)
        missing = missing_inputs(q, authorities)
        proposal = provider.propose(q, authorities) if not missing else RulesProvider().propose(q, authorities)
        if not isinstance(proposal, dict) or not isinstance(proposal.get("supporting"), str) or not isinstance(proposal.get("opposing"), str) or not isinstance(proposal.get("unknowns"), list):
            raise ValueError("invalid provider proposal")
        items.append({
            "question_id": q["id"], "finding_id": q["finding_id"], "issue_type": q["issue_type"],
            "status": "insufficient_information" if missing else "review_pending",
            "reasons": ["Legal analysis and applicability require lawyer review."],
            "missing": missing, "contract_evidence": verified_contract_evidence(project, q["evidence"]),
            "authority_ids": [a["id"] for a in authorities], "authorities": authorities,
            "facts": fact_summary(q), "dependencies": map_dependencies(project, q),
            "provider_draft_unreviewed": proposal, "provider": getattr(provider, "name", type(provider).__name__),
            "lawyer_review": "pending", "outcome_probability": None,
        })
    result = {"schema": SCHEMA, "source_sha256": project["source_sha256"],
              "project_version": project["version"], "request_sha256": fingerprint(request),
              "manifest_sha256": fingerprint(manifest), "assessments": items}
    validate_assessment(project, review, request, result, manifest)
    return result
