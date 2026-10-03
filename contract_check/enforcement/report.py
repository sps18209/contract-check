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
                 "**Legal review:** Analyze the asserted obligation, alternative reading, defenses, and remedy against the cited source text.", "",
                 "**Missing inputs:** " + (_safe(", ".join(item["missing"])) or "None recorded"), "",
                 "**Supplied authorities:** " + (_safe(", ".join(item["authority_ids"])) or "None"), "",
                 "**Provider draft:** Omitted from this report pending lawyer review of its claims.", ""]
        for authority in item["authorities"]:
            rows += [f"- {_safe(authority['id'])}: {_safe(authority['title'])} ({_safe(authority['jurisdiction'])}; {_safe(authority['court_or_body'])}; {_safe(authority['decision_date'])}) — {_safe(authority['source_url'])}",
                     f"  Excerpt in supplied text: {_safe(authority['excerpt'])}. Reviewer attested: {_safe(authority['reviewer_verified'])}."]
        rows.append("")
        for state, facts in item["facts"].items():
            for fact in facts:
                rows.append(f"- Fact ({_safe(state)}): {_safe(fact['statement'])} [source: {_safe(fact['source'])}]")
        rows += ["", "**Cross-references:** " + (_safe(", ".join(link["reference"] for link in item["dependencies"]["explicit_references"])) or "None identified"), ""]
    return "\n".join(rows).rstrip() + "\n"
