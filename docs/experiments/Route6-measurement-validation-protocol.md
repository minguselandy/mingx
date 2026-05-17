# Route 6 Measurement-validation Protocol

Status: protocol freeze only
Claim status: `no_claim_upgrade`

Route 6 defines the external validation program required before measurement
validation evidence can be considered. It does not run annotation or adjudication
in this package.

## Validation Sources

Route 6 uses a hybrid validation design:

- external strong-model adjudication for broad, repeatable adjudication;
- human sentinel annotation for calibration and error discovery;
- hybrid adjudication where human labels arbitrate strong-model disagreement or
  low-confidence cases.

Strong-model adjudication alone is not measurement validation evidence. Human or
hybrid evidence, agreement metrics, contamination review, and bias audit are all
required before a validation candidate can be considered.

## Annotation Rubric

The rubric must predeclare:

- task target and answer or label representation;
- evidence sufficiency labels;
- evidence relevance labels;
- source-document coverage labels;
- answer correctness labels where applicable;
- uncertainty and abstention handling;
- invalid or contaminated item handling;
- adjudication escalation rules.

Each annotation item must preserve dataset, split, candidate-pool hash,
packet IDs, materialized context hash, annotator or adjudicator provenance, and
rubric version.

## Agreement Metrics

Route 6 must report:

- pairwise human agreement;
- Cohen or Fleiss kappa where the label structure permits;
- Krippendorff alpha for mixed or missing-label settings;
- human versus strong-model agreement;
- adjudication override rate;
- bootstrap confidence intervals for the primary validation metric.

Agreement metrics must be computed before any measurement validation candidate
is proposed.

## Contamination Audit

The contamination audit must cover:

- benchmark leakage into evaluator prompts or examples;
- public answer-key exposure;
- repeated use of the same items in prompt tuning;
- annotator access to gold labels outside the rubric;
- strong-model memorization risk;
- overlap between training, development, and heldout validation sets.

Contaminated items must be excluded or marked with a fail-closed status.

## Model-bias Audit

The model-bias audit must include:

- strong-model versus human disagreement sampling;
- error slices by answer type, task family, source length, and difficulty;
- adversarial or low-evidence cases;
- annotation fatigue checks;
- systematic preference for longer or more confident evidence packets;
- reviewer audit of a bounded sample of model-only decisions.

## Validation Gates

Route 6 may propose:

```text
measurement_validation_candidate
```

only if:

- annotation rubric is frozen before labeling;
- human sentinel sample size is met;
- agreement metrics pass predeclared thresholds;
- contamination audit passes;
- model-bias audit does not identify unresolved systematic failure;
- bridge/proxy dependencies required for the paper claim are satisfied;
- independent review accepts the validation package.

Final measurement validation evidence requires review beyond the candidate
state.

## Stop Conditions

Stop Route 6 if:

- annotator instructions change after labels are collected;
- agreement metrics fall below thresholds;
- contamination cannot be bounded;
- model-only labels are substituted for required human sentinel evidence;
- strong-model errors cluster in a high-risk slice;
- claim wording treats model adjudication as human validation.
