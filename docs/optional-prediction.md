# Optional prediction module

The ordinary review is deterministic in its gates and evidence records. It does not call a prediction provider. The existing `contract_check.enforcement.prediction` package is an offline experiment with an optional scikit-learn dependency; it is not an enforceability scorer for individual agreements.

Run only with an appropriately sourced and authorized labeled dataset:

```sh
python -m pip install '.[prediction]'
python -m contract_check prediction-experiment outcomes.json evaluation.json --enable-research-prediction
```

Without the explicit flag, the command fails. The dataset validator requires a defined event, population, forum, posture, horizon, adjudicated outcomes, label provenance, and pre-outcome features. The experiment separates training, calibration, and test cohorts in time, compares Brier score with a prevalence baseline, and emits research metrics and limitations. It does not serialize a deployable model or return an individual forecast.

A future user-facing toggle should be an independent adapter, never a step in `assess`, `apply`, or the normal report. Its interface should accept an authorized cohort and a specific event definition, and return `insufficient_evidence` by default. Release requires independently reviewed labels, sufficient relevant subgroup support, leakage and selection-bias analysis, time-split calibration, held-out performance, drift checks, attorney review of the output, and clear communication of uncertainty. The legal assessment must remain available with the toggle off. Never treat model confidence, similarity, Jev scores, or a benchmark score as a probability of enforcement.

For a nearer-term predictive feature, a separately validated reviewer-triage model could estimate whether a *reviewer will flag a draft-to-instruction mismatch*. It would require labeled reviewer decisions and its own event definition; that estimate is about review priority, not legal outcome. No Jev API key is needed for the current package. A hosted adapter would require user authorization and separate privacy, cost, and validation choices.
