# Operator Dry-Run Rehearsal

**Phase:** P30 Operator-Approved Dry-Run Rehearsal

**Status:** Offline dry-run rehearsal only. P30 does not run live APIs, call
external model providers, import external SDKs, fabricate human labels, fabricate
kappa, fabricate contamination pass, or claim `measurement_validated`.

## 1. Purpose

P30 proves that the controlled empirical validation workflow can produce a
dry-run evidence package before any live operator execution. It wires the
existing P26-P28 function/API layers together:

```text
P26 controlled live pilot dry-run
  -> P27 empty human-label templates and missing-kappa report
  -> P28 unknown contamination report
  -> P28 empirical evidence package
  -> P30 rehearsal manifest and summary
```

The rehearsal is part of the CPS measurement and runtime-audit scaffold. It is
not a general agent framework and not live empirical validation.

## 2. Relationship To P25-P29

- P25 defines the EV0-EV4 empirical validation ladder.
- P26 provides the controlled live pilot runner with `dry_run` as the default.
- P27 provides human-label templates, completeness checks, and kappa reports.
- P28 packages pilot, label, kappa, contamination, and bridge evidence.
- P29 defines the operator runbook for future DeepSeek V4 Flash / Pro live
  pilot operations.
- P30 rehearses that chain offline with deterministic local artifacts only.

## 3. Dry-Run Model Conditions

The rehearsal includes:

| Model alias | Role | Cases | Behavior |
| --- | --- | --- | --- |
| `deepseek_v4_flash` | `primary_pilot_model` | `case-001`, `case-002` | Dry-run placeholder condition only. |
| `deepseek_v4_pro` | `strong_model_audit_subset` | `case-001` | Dry-run matched subset only. |

No real provider model IDs are required. The generated manifest uses placeholder
endpoint and model-name fields. DeepSeek V4 Flash / Pro are dry-run model
conditions only and are not validation authorities.

## 4. Conditions And Case Set

Required conditions:

- `no_cps_baseline`
- `heuristic_selector_baseline`
- `cps_runtime_audit_scaffold`

The fixture is intentionally tiny. It is suitable for deterministic rehearsal
tests, not empirical power or external validity.

## 5. How To Run

P30 exposes a function/API, not a CLI:

```python
from pathlib import Path

from cps.experiments.operator_dry_run_rehearsal import build_operator_dry_run_rehearsal

result = build_operator_dry_run_rehearsal(Path("artifacts/experiments/p30-dry-run"))
```

Do not run this as live execution. It does not require `CPS_ALLOW_LIVE_API=1`
and does not call a provider.

## 6. Output Files

The output root contains:

- `dry_run_manifest.json`
- `pilot_summary.json`
- `case_artifacts/`
- `human_labels_template.csv`
- `human_labels_template.jsonl`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_evidence_manifest.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`
- `rehearsal_summary.json`
- `rehearsal_summary.md`

P28 also writes `live_pilot_summary.json`, `kappa_report.md`, and
`contamination_report.md` as supporting deterministic artifacts.

## 7. Claim Boundary

P30 deliberately leaves validation-critical evidence missing:

- `live_api_used: false`
- `external_runtime_used: false`
- `human_labels_present: false`
- `labels_complete: false`
- `kappa_present: false`
- contamination status is unknown by default
- metric bridge freshness is missing by default
- `measurement_validated_allowed: false`

Missing labels deny `measurement_validated`. Missing kappa denies
`measurement_validated`. Unknown or incomplete contamination denies
`measurement_validated`. Missing or stale metric bridge evidence remains
`operational_utility_only` or `ambiguous`.

Dry-run artifact completeness is engineering/rehearsal evidence only. It is not
live empirical validation and not scientific validation.

## 8. Determinism

The rehearsal is deterministic:

- no timestamps;
- no UUIDs;
- no randomness;
- no network calls;
- no external SDK imports;
- stable model ordering;
- stable case ordering;
- stable condition ordering;
- stable reason-code ordering;
- stable JSON serialization;
- stable Markdown output.

Repeated runs with the same input produce byte-identical top-level JSON and
Markdown outputs.

## 9. Preparing For Operator-Approved Live Execution

P30 prepares the operator by confirming that artifact plumbing works before live
execution. The next live decision still requires:

- an operator-approved live manifest;
- fixed model endpoint and model name;
- fixed model alias;
- frozen prompt templates;
- fixed case set and condition assignment;
- budget cap;
- credentials configured outside the repo;
- contamination reviewer;
- metric bridge reviewer;
- labeler availability for EV3.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`.

## 10. Next Phase

Recommended next phase:

```text
P31 Operator-Approved Live Pilot Execution Decision
```

P31 should decide whether operators approve live execution. It must not treat P30
dry-run completion as live validation.
