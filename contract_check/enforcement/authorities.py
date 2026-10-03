"""Verify supplied passages against supplied source text, not legal correctness."""

import hashlib


def verify_manifest(manifest: dict) -> dict[str, dict]:
    if not isinstance(manifest, dict) or manifest.get("schema") != 1 or not isinstance(manifest.get("authorities"), list):
        raise ValueError("invalid authority manifest")
    result = {}
    for item in manifest["authorities"]:
        if not isinstance(item, dict):
            raise ValueError("invalid authority")
        fields = ("id", "title", "jurisdiction", "court_or_body", "decision_date", "precedential_status", "source_url", "full_text", "excerpt")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in fields):
            raise ValueError("authority missing provenance field")
        if item["id"] in result or item["excerpt"] not in item["full_text"]:
            raise ValueError("duplicate authority or excerpt missing from source text")
        if type(item.get("reviewer_verified", False)) is not bool:
            raise ValueError("reviewer_verified must be Boolean")
        result[item["id"]] = {key: item[key] for key in fields if key != "full_text"}
        result[item["id"]]["reviewer_verified"] = item.get("reviewer_verified", False)
        result[item["id"]]["source_sha256"] = hashlib.sha256(item["full_text"].encode("utf-8")).hexdigest()
        result[item["id"]]["verification"] = "excerpt_in_supplied_text"
    return result


def resolve_authorities(question: dict, manifest: dict) -> list[dict]:
    verified = verify_manifest(manifest)
    ids = question.get("authority_ids", [])
    if len(ids) != len(set(ids)) or any(key not in verified for key in ids):
        raise ValueError("unverified authority id")
    return [verified[key] for key in ids]
