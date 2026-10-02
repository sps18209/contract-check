# Evidence-linked review record

Create a JSON record containing `source_sha256`, `project_version`, `context`, and `findings`. Context contains string fields `contract_type`, `represented_party`, `objective`, `jurisdiction`. Write `unknown` where necessary. An empty findings list means no issues were identified within stated scope, not that the contract is safe.

Each finding contains: unique `id`; `lens` (`deal`, `linguistic`, `philosophical`, `operational`, `structural`, `definitions`, `termination`, or `legal`); `status` (`proposed`, `accepted`, `rejected`, `deferred`, `resolved`); an `evidence` array of `{block_id, quote}` where quote occurs verbatim in the current block; `affected_blocks` array; and strings `issue`, `consequence`, `proposal`, `uncertainty`, `decision_needed`. For a missing-section finding, set `evidence: []` and provide a substantive `absence_basis` explaining what was searched and what external instruction calls for the clause. Use an empty affected array if impact is unknown. Include alternative plausible readings in `issue` when the text admits them. Record negotiated-term evidence separately from the draft text.

The validator checks record shape, version, and passage provenance. It cannot confirm legal accuracy, completeness, deal fidelity, or whether an excerpt supports the inference. Run a separate semantic verification against the original and user-approved decisions. Present each finding as a proposal until the user selects a disposition.

Example:

```json
{
  "source_sha256": "<project source hash>",
  "project_version": 1,
  "context": {"contract_type": "services", "represented_party": "customer", "objective": "predictable exit", "jurisdiction": "unknown"},
  "findings": [{
    "id": "F-1", "lens": "termination", "status": "proposed",
    "evidence": [{"block_id": "b00004", "quote": "30 days after notice"}],
    "affected_blocks": ["b00004"],
    "issue": "The event starting the notice period is unclear.",
    "consequence": "The parties may calculate different termination dates.",
    "proposal": "Specify delivery or receipt and its relationship to the cure period.",
    "uncertainty": "The negotiated trigger is unknown.",
    "decision_needed": "Choose the intended trigger and cure sequence."
  }]
}
```
