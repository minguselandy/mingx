# P55 New-Stratum Bridge Calibration Pilot

## Status

P55 is a bounded importer and claim-gated bridge-pilot scaffold for the P54-approved stratum:

`evidence_packet_selection_microtask_v1`

The operator approved Route A for operator-imported rows only. This approval does not authorize live API execution, credentials, human-labeled rows, human-human kappa, measurement validation, deployed V-information verification, or any claim upgrade outside the P55 gates.

## Active Stratum Binding

Every imported row must match the P54 design and P53 diagnostic threshold contract:

- `stratum_id`: `evidence_packet_selection_microtask_v1`
- `task_family`: `evidence_packet_selection_microtask_v1`
- `data_source_kind`: `operator_imported_rows`
- materialization policy: `fixed_order_evidence_packet_v1`
- model tier: `fixed_evaluated_model_tier`
- decoding policy: `deterministic_logloss_scoring_no_generation`
- candidate slice band: `top_8_candidate_packets_fixed_before_projection`
- target type: `forced_choice_or_exact_field`
- logloss measurement: `fixed_model_target_logloss_for_declared_answer`
- bridge contract: `diagnostic_threshold_contract_v12_template`

If any binding fails, the pilot fails closed to `ambiguous_metric` or `operational_utility_only` with `paper_evidence_eligible: false`.

## Required Row Fields

The importer requires the P55 row fields declared in:

`configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-p55.json`

The required fields include dispatch identity, candidate-pool hash, projection/context hashes, block identity, materialization/model/decoding policy, target evidence, measured `delta_logloss`, `delta_utility`, utility metric version, replicate count, effective sample size, data source kind, contamination status, bridge contract id, stratum metadata, logloss measurement version, and operator approval reference.

## Fit and Held-Out Reporting

When valid rows are present, P55:

- fits `c_s` on the development split only;
- reports `zeta_s` as a held-out residual bound;
- reports held-out sign agreement;
- reports held-out Spearman/rank correlation;
- reports effective sample size;
- records drift and bridge-witness status;
- records active-stratum and candidate-pool hash status;
- applies a deterministic claim gate.

Rows may declare `split: dev` or `split: heldout`. If no split is declared, the importer uses a deterministic stable half split. If the held-out split is unavailable or underpowered, the result fails closed.

## Current Data Source Status

No operator-imported P55 row file was present at the configured path during this run:

`artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl`

P55 therefore produced a blocked fail-closed report instead of fabricating rows or claiming a successful bridge.

The no-row gate treats an absent operator-input file, an existing empty input file, and a blank/comment-only input file as the same no-row condition:

- input file status: `absent` or `empty`
- rows imported: `0`
- rows validated: `0`
- claim gate result: `failed_closed_no_rows`
- pilot status: `blocked_operator_required`
- review ceiling: `none`
- paper evidence eligible: `false`
- fit metrics computed: `false`

## Generated Outputs

Current canonical outputs:

- `artifacts/experiments/p55_bridge_calibration_pilot/manifest.json`
- `artifacts/experiments/p55_bridge_calibration_pilot/claim_gate_report.json`
- `artifacts/experiments/p55_bridge_calibration_pilot/report.md`

If contract-compliant operator-imported rows are later supplied and independently reviewed, the importer can also emit:

- `validated_rows.jsonl`
- `bridge_fit_summary.json`
- `bridge_fit_summary.csv`

## Claim Gate

The current P55 result is fail-closed because operator-imported rows are absent. Empty operator-input files also fail closed under the same no-row semantics.

Current result:

- pilot status: `blocked_operator_required`
- metric claim level: `ambiguous_metric`
- paper evidence eligible: `false`
- measurement validation claim: `false`
- live API used: `false`
- human labels present: `false`
- human-human kappa present: `false`

`calibrated_proxy_supported` is allowed only for the exact active stratum if all P55 gates pass on contract-compliant operator-imported rows. `vinfo_proxy_supported` is not authorized by P55 without a separate formal/fixed-model bridge review.

## Claim Boundaries

P55 does not claim:

- measurement validation
- human-label validation
- human-human kappa
- deployed V-information verification
- theorem-level deployed submodularity verification
- synthetic evidence as bridge evidence
- fixture evidence as paper-grade evidence
- replay usability as metric support
- extraction audit as selector validity
- `ReprojectionWitness` as deployed runtime improvement
- current P45 `bio_attribute` as `calibrated_proxy_supported`
- P55 fixture/test rows as `calibrated_proxy_supported`
- `vinfo_proxy_supported` without explicit formal bridge review

The current P45 `bio_attribute` stratum remains non-calibrated and fail-closed.
