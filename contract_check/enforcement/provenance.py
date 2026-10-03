"""Reject stale, invented, or unattributed contract quotations."""

from ..core import validate


def verified_contract_evidence(project: dict, evidence: list[dict]) -> list[dict]:
    validate(project)
    blocks = {b["id"]: b["text"] for b in project["blocks"]}
    verified = []
    for row in evidence:
        if not isinstance(row, dict) or row.get("block_id") not in blocks or not isinstance(row.get("quote"), str) or not row["quote"] or row["quote"] not in blocks[row["block_id"]]:
            raise ValueError("unverified contract quotation")
        verified.append({"block_id": row["block_id"], "quote": row["quote"]})
    return verified
