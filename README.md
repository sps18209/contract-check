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
python -m unittest discover -s tests -v
```

The `plan.json` and review record formats are documented in `skill/references/`. Text extraction from DOCX/PDF, substantive legal analysis, current-law research, and export are host capabilities, not implemented by the engine. Do not run client documents through a third-party service without appropriate authorization. This is not yet a certified annual edition or a ready-to-sell product.

## Development sequence

The initial release establishes provenance, deliberate edits, structure choices, mechanical checks, and a review-record contract. Next: richer paragraph/table extraction and document fidelity; multi-part cross-references and definitions inventory; user-facing choice cards and output rendering; representative deal-to-draft and semantic-drift evaluations across contract types; host-specific packaging and installation verification; lawyer review and edition sign-off. Track commercial licensing of third-party source material separately; the Contract Navigator textbook is not included.
