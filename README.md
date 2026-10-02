# Contract Check

An early contract-review skill and auditable structural engine. The skill lives in `skill/`; the Python package lives in `contract_check/`. The engine performs deterministic text and numbering operations. Substantive review is directed by the skill and remains subject to human legal judgment.

## Local use

```sh
python -m contract_check ingest agreement.txt project.json
python -m contract_check apply project.json plan.json revised.json
python -m contract_check render revised.json revised.txt --style decimal --update-refs --map-output map.json
python -m contract_check check revised.json revised.txt
python -m contract_check compare project.json revised.json changes.json
python -m contract_check audit project.json revised.json flags.json
python -m contract_check validate-review revised.json review.json
python -m contract_check extract-docx agreement.docx agreement.txt extraction.json
python -m contract_check cards revised.json review.json choices.md
python -m contract_check choice-template revised.json review.json choices.json
python -m contract_check validate-choices revised.json review.json choices.json
python -m contract_check inventory project.json inventory.json
python -m contract_check preview revised.json structure.md
python -m contract_check report project.json revised.json report.md
python -m unittest discover -s tests -v
```

The `plan.json` and review record formats are documented in `skill/references/`. The DOCX extractor provides ordered plain text and an inspection manifest; it does not preserve layout or every ancillary part. PDF/image extraction, current-law research, and document export depend on host capabilities. Substantive review is guided by the skill and requires human verification. Do not run client documents through a third-party service without appropriate authorization. This is not yet a certified annual edition or a ready-to-sell product.

Build a self-contained skill bundle with `python scripts/build_skill.py /tmp/contract-check.skill --edition-year 2026`. The archive includes the skill instructions, review references, a standard-library Python runtime under `scripts/`, and a per-file hash manifest marking lawyer review as pending. It does not require the repository after extraction. It does not include the Contract Navigator textbook or any credentials. The storefront and re-download entitlements remain separate work.

## Development sequence

The development release establishes provenance, deliberate edits, structure and decision choices, mechanical checks, a review-record contract, DOCX text extraction, and self-contained packaging. Remaining gates: broader document fidelity and references; independent review on unseen and real sanitized contracts; host-specific installation and export verification; lawyer review and edition sign-off. Track commercial licensing of third-party source material separately; the Contract Navigator textbook is not included.

## Evaluation

`evaluation/cases.json` contains four fictional transactions: services, software licensing, data processing, and a property option. Export reviewer-facing prompts with `python evaluation/export_prompts.py /tmp/contract-check-prompts`. The answer key remains in the source file for later assessment. `python evaluation/score_reviews.py RESPONSES SCORE.json` checks response provenance, expected passage citation, and preservation of specified terms; follow `evaluation/protocol.md` for human review of substance, restraint, and decisions. Passing these synthetic cases does not establish performance on actual client agreements.
