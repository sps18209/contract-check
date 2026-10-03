"""Plain Markdown issue cards for a lawyer's review."""


def _safe(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def render_assessment(result: dict) -> str:
    rows = ["# Enforcement issue assessment", "", "Provisional issue analysis. No legal outcome probability has been estimated.", "",
            f"Source SHA-256: `{result['source_sha256']}` · Version: {result['project_version']}", ""]
    for item in result["assessments"]:
        rows += [f"## {_safe(item['question_id'])} · {_safe(item['issue_type'])}", "",
                 f"**Status:** {_safe(item['status'])} · Lawyer review: {_safe(item['lawyer_review'])}", "",
                 "**Contract text:** " + "; ".join(_safe(e["block_id"] + ": " + e["quote"]) for e in item["contract_evidence"]), "",
                 "**Supporting question:** " + _safe(item["supporting_hypothesis"]), "",
                 "**Opposing question:** " + _safe(item["opposing_hypothesis"]), "",
                 "**Missing inputs:** " + (_safe(", ".join(item["missing"])) or "None recorded"), "",
                 "**Supplied authorities:** " + (_safe(", ".join(item["authority_ids"])) or "None"), "",
                 "**Unresolved:** " + _safe("; ".join(item["unresolved_questions"])), ""]
    return "\n".join(rows).rstrip() + "\n"
