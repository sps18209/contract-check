"""Trace explicit references and adjacent conditional language for review."""

import re

from ..core import validate

_REF = re.compile(r"\b(?:Section|Article)\s+\d+(?:\.\d+)*\b", re.I)
_CONDITION = re.compile(r"\b(?:if|unless|subject to|provided that|only after|upon)\b", re.I)


def map_dependencies(project: dict, question: dict) -> dict:
    validate(project)
    selected = {row["block_id"] for row in question["evidence"]}
    blocks = {b["id"]: b["text"] for b in project["blocks"]}
    links = []
    for block_id in selected:
        text = blocks[block_id]
        links.extend({"from_block": block_id, "reference": match.group(), "target_status": "unresolved"}
                     for match in _REF.finditer(text))
    return {"explicit_references": links,
            "conditional_language": [bid for bid in selected if _CONDITION.search(blocks[bid])],
            "note": "Candidate links only; verify referenced provisions and triggering facts manually."}
