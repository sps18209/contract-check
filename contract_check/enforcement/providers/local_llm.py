"""Explicit loopback-only JSON adapter for a locally hosted chat completions API."""

import json
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("local model endpoint attempted a redirect")


class LocalLLMProvider:
    name = "local-llm-v1"

    def __init__(self, endpoint: str, model: str):
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1") or parsed.path != "/v1/chat/completions" or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("local model endpoint must be a loopback HTTP chat completions URL")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model name required")
        self.endpoint, self.model = endpoint, model

    def propose(self, question: dict, authorities: list[dict]) -> dict:
        payload = {
            "model": self.model, "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return only JSON with string keys supporting, opposing, and array unknowns. Propose competing legal questions using only supplied text. Do not claim authority is verified current law. Do not estimate probability or declare enforceability."},
                {"role": "user", "content": json.dumps({"question": question, "authorities": authorities}, ensure_ascii=False)},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = Request(self.endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with build_opener(ProxyHandler({}), _NoRedirect()).open(req, timeout=30) as response:
            if response.headers.get("Content-Length") and int(response.headers["Content-Length"]) > 2_000_000:
                raise ValueError("local model response too large")
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("local model response too large")
        body = json.loads(raw)
        proposal = json.loads(body["choices"][0]["message"]["content"])
        if not isinstance(proposal, dict) or not all(isinstance(proposal.get(k), str) for k in ("supporting", "opposing")) or not isinstance(proposal.get("unknowns"), list) or any(not isinstance(x, str) for x in proposal["unknowns"]):
            raise ValueError("invalid local model proposal")
        if any(k in proposal for k in ("probability", "outcome_probability", "status")):
            raise ValueError("model attempted to set a legal outcome or probability")
        return {k: proposal[k] for k in ("supporting", "opposing", "unknowns")}
