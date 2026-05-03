# Empirical Evidence Package

**Phase:** P28 Contamination and Live Evidence Package Integration, extended by
P36 Model-Adjudicated Evidence Package Integration

**Status:** Empirical evidence packaging and gating layer. P28 does not execute
live APIs, collect labels, compute new kappa from fabricated labels, or complete
empirical validation.

## 1. Purpose

P28 integrates future empirical evidence artifacts into one deterministic
package:

```text
controlled live pilot summary
  -> Route A: human label completeness report and kappa report
  -> Route B: V4 Flash prelabels, Codex audit, and model-adjudicated labels
  -> contamination report
  -> metric bridge freshness status
  -> empirical claim gate summary
  -> empirical evidence package
```

The package extends the CPS runtime-audit evidence stack. It does not replace
the existing conservative claim gate.

## 2. Inputs

The builder consumes either an in-memory mapping or a P26-style output directory.

Supported inputs include:

- `run_manifest.json`
- `pilot_summary.json`
- `claim_gate_report.json`
- `evidence_ledger.json`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `llm_prelabels.jsonl`
- `subagent_audit_report.json`
- `model_adjudicated_labels.jsonl`
- `codex_adjudication_report.json`
- `model_adjudicated_label_summary.json`
- metric bridge freshness status
- artifact completeness status

For Route A, missing label, kappa, contamination, or bridge artifacts fail
closed. For Route B, absent human labels and absent human-human kappa must remain
explicitly recorded and must block `measurement_validated`. Missing evidence does
not become validation evidence in either route.

## 3. Two Evidence Routes

The empirical package can consume two distinct evidence routes.

| Route | Inputs | Required claim boundary |
| --- | --- | --- |
| Route A: human-label route | Human labels, kappa report, contamination report, metric bridge freshness, claim gate report. | Human labels and human-human kappa may support `measurement_validated_candidate` only when all other gates also pass. |
| Route B: model-adjudicated route | V4 Flash prelabels, Codex subagent audit, model-adjudicated labels, contamination audit, metric bridge status, claim gate report. | Keep `human_labels_present=false`, `kappa_present=false`, and `measurement_validated_allowed=false`; allowed claim is no stronger than `model_adjudicated_pilot_only` or `operational_utility_only`. |

Route B does not produce `human_labels.jsonl`, does not establish human-human
kappa, and does not replace Route A. It is an automated judge evidence path for
pilot and operational analysis only.

## 4. Route B: Model-Adjudicated Evidence Package

Route B package support consumes:

- `llm_prelabels.jsonl`;
- `subagent_audit_report.json`;
- `model_adjudicated_labels.jsonl`;
- `codex_adjudication_report.json`;
- `model_adjudicated_label_summary.json`;
- `contamination_report.json`;
- metric bridge freshness status;
- claim gate status.

Route B package outputs include route fields in:

- `empirical_evidence_manifest.json`;
- `empirical_claim_gate_report.json`;
- `empirical_evidence_summary.md`.

The Route B fields include:

- `route_type: model_adjudicated`;
- `evaluation_route: Route_B_model_adjudicated`;
- `llm_prelabels_present`;
- `subagent_audit_present`;
- `codex_adjudication_report_present`;
- `model_adjudicated_labels_present`;
- `model_adjudicated_label_count`;
- `model_adjudicated_label_summary_present`;
- `human_labels_present: false`;
- `kappa_present: false`;
- `human_human_kappa_established: false`;
- `measurement_validated_allowed: false`.

Human labels are not required for Route B because Route B is not a human-labeled
measurement validation route. This is a convenience for automated pilot analysis,
not a validation shortcut. Since Route B does not produce human labels and does
not compute human-human kappa, `measurement_validated` is impossible for Route B.

Route B differs from Route A as follows:

| Feature | Route A | Route B |
| --- | --- | --- |
| Label source | Human annotators. | V4 Flash prelabels plus Codex model adjudication. |
| Human-human kappa | Required. | Not produced. |
| Maximum claim | `measurement_validated_candidate` if all gates pass. | `model_adjudicated_pilot_only` or `operational_utility_only`. |
| Paper use | Human-labeled pilot or validation-candidate evidence. | Model-adjudicated pilot evidence, operational utility evidence, or annotation workload reduction evidence. |

Route B reason codes explicitly preserve the boundary:

- `route_b_model_adjudicated`;
- `model_adjudicated_labels_not_human_labels`;
- `codex_adjudication_not_human_review`;
- `human_labels_not_required_for_route_b`;
- `human_labels_missing_for_measurement_validation`;
- `human_kappa_missing_for_measurement_validation`;
- `measurement_validated_denied_for_route_b`;
- `route_b_max_claim_boundary`.

## 5. Outputs

The package can write:

- `empirical_evidence_manifest.json`
- `live_pilot_summary.json`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`

The manifest records:

- controlled live run presence;
- live API usage;
- human-label completeness;
- kappa status;
- contamination status;
- metric bridge freshness;
- artifact completeness;
- allowed empirical claim level;
- denied claims;
- stable reason codes;
- P04/P09 status.

## 6. Claim Mapping

| Evidence state | Allowed empirical claim level |
| --- | --- |
| No controlled live run | `not_empirical_validation` |
| Live run without labels | `controlled_live_pilot_only` |
| Missing labels | Not `measurement_validated` |
| Missing kappa | Not `measurement_validated` |
| Low kappa | `pilot_only` or weak evidence |
| Contamination failed | `pilot_only` |
| Contamination unknown/incomplete | Not `measurement_validated` |
| Stale bridge | `operational_utility_only` |
| Missing bridge | `ambiguous` |
| Route B with V4 Flash prelabels, Codex audit, and model-adjudicated labels | At most `model_adjudicated_pilot_only` or `operational_utility_only` |
| Route B with contamination failure | `pilot_only` |
| Route B with missing bridge | `ambiguous` |
| Route B with stale bridge | `operational_utility_only` |
| High kappa, contamination pass, fresh bridge, complete artifacts | At most `measurement_validated_candidate` unless the existing claim gate explicitly allows more. |

Even favorable evidence remains a candidate until all external requirements and
the existing claim gate allow a stronger claim.

For Route B, `measurement_validated`, `human_labeled_validation`,
`human_human_kappa_established`, scientific validation, and deployed
V-information certification remain denied.

## 7. Relationship To P26, P27, P32, P34, And P36

P26 provides controlled live pilot scaffolding and case artifacts. P27 provides
human-label completeness and kappa reports. P28 packages those reports with
contamination and metric bridge evidence.

P32 provides V4 Flash prelabels and Codex subagent audit requests/reports. P34
provides model-adjudicated labels. Those artifacts may be packaged as Route B
evidence, but they must not satisfy human-label or kappa gates.

P36 integrates Route B into the empirical package output manifest, empirical
claim gate report, and Markdown summary. It does not loosen Route A validation
gates.

P28 does not:

- run the P26 live mode;
- call a model API;
- fabricate labels;
- fabricate kappa;
- fabricate contamination clearance;
- convert model-adjudicated labels into human labels;
- unblock P04 or P09.

## 8. Claim Boundary

- P28 does not complete empirical validation.
- Live API success alone is not measurement validation.
- Human labels and acceptable kappa are required.
- Route B model-adjudicated labels are not human labels.
- Route B does not establish human-human kappa.
- Route B cannot support `measurement_validated`.
- High kappa alone is not measurement validation.
- Contamination pass alone is not measurement validation.
- Fresh metric bridge evidence is required.
- Existing claim gate approval is required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed by default.
