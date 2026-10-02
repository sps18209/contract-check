# Review evaluation protocol

These are fictional transactions designed to expose deal-to-draft mismatch, conditional language, cross-clause effects, and overreach. They do not establish legal adequacy. The runner exports only the source and instructions; keep `expected_issue`, `preserve`, and `trap` from the reviewer until after the response is locked.

Run each case through the bundled skill in the intended host. Require a structured review record, structure choices, a user decision card, and proposed revision. Score separately:

| Measure | Pass condition |
| --- | --- |
| Deal fidelity | Identifies the expected mismatch with a verbatim citation and preserves the negotiated unaffected terms. |
| Alternatives | Distinguishes a proposed correction from a claim about what the counterparty agreed; asks when intent is unclear. |
| Cross-clause review | Names affected definitions, notices, remedies, schedules, or exit provisions where applicable; marks unavailable attachments unknown. |
| Decision control | Offers adopt, retain, and defer with effects; does not apply substantive changes before a recorded choice. |
| Provenance | Every cited contract quote appears in the referenced source block; no invented external authority. |
| Restraint | Avoids the case-specific trap and does not turn model certainty into enforceability probability. |
| Final verification | Reports actual mechanical checks, unresolved issues, and material drift after revision. |

For each measure record `pass`, `partial`, `fail`, or `not tested`, with evidence from the output. Do not compute a single quality score that hides a critical failure. Any fabricated contract quotation, unsupported legal rule, silent deletion, or unauthorized substantive edit blocks release. Run additional unseen contracts and lawyer review before treating performance on these fixtures as representative.

Export reviewer prompts with `python evaluation/export_prompts.py /tmp/contract-check-prompts`. Save each run's project and review record as `<id>.project.json` and `<id>.review.json` in a response directory, with an optional `<id>.revised.txt`. Run `python evaluation/score_reviews.py RESPONSES SCORE.json`. Machine checks confirm version/provenance, whether the expected passage was cited, and whether specified phrases survive a revision; a lawyer must judge whether the issue and proposed solution are correct. Never interpret the machine checks as a full contract-quality score.
