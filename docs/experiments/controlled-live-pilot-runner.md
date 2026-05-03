# Controlled Live Pilot Runner

**Phase:** P26 Controlled Live API Pilot Runner Design

**Status:** Guarded EV2 scaffold. The default mode is dry-run. This document
does not authorize a live API run.

## 1. Purpose

P26 adds a controlled live pilot runner scaffold for future EV2 empirical
validation planning. It packages the execution path:

```text
run_manifest
  -> case loading
  -> condition assignment
  -> projection artifact capture
  -> model output capture
  -> claim gate report
  -> live evidence package
```

The runner is part of the CPS measurement and runtime-audit scaffold. It is not a
general agent framework and does not implement a vendor API client.

## 2. Runner Modes

| Mode | Default? | Live API behavior | Claim boundary |
| --- | --- | --- | --- |
| `dry_run` | yes | No live calls. Deterministic local model-output placeholders are written. | Engineering/pilot scaffold only. |
| `live_operator_approved` | no | Calls only the injected `model_call_fn`, and only after all live gates pass. | Controlled pilot only; not measurement validation. |

Unit tests must not call live APIs. They use deterministic fake callables only.

## 3. Live Gates

Live mode fails closed before any model call unless all of the following are
present:

- `CPS_ALLOW_LIVE_API=1`
- explicit `run_manifest_path`
- fixed `model_endpoint`
- fixed `model_name`
- frozen `prompt_template_id`
- fixed `temperature`
- `output_root`
- `operator_approval: true`
- injected `model_call_fn`

The runner does not import external SDKs and does not implement OpenAI, DeepSeek,
Qwen, OpenRouter, vLLM, or other vendor-specific clients.

## 4. Manifest Fields

The run manifest records:

- `run_id`
- `evidence_level: EV2_controlled_live_pilot`
- `mode`
- `model_endpoint`
- `model_name`
- `prompt_template_id`
- `temperature`
- `max_cases`
- `conditions`
- `output_root`
- `operator_approval`
- `live_api_used`
- `external_runtime_used`
- `human_labels_required_for_measurement_validated`
- `kappa_required_for_measurement_validated`
- `contamination_audit_required`
- `metric_bridge_freshness_required`

The manifest defaults to dry-run and sets `live_api_used: false`.

## 5. Experimental Conditions

Required conditions:

- `no_cps_baseline`
- `heuristic_selector_baseline`
- `cps_runtime_audit_scaffold`

Optional condition:

- `full_context_upper_baseline`

Each condition writes the same artifact set so replay, claim gates, and future
labeling can compare conditions without changing artifact semantics.

## 6. Case Artifacts

For each `(case, condition)` dispatch, the runner writes:

- `input_case.json`
- `candidate_pool.jsonl`
- `projection_plan.json`
- `budget_witness.json`
- `materialized_context.json`
- `metric_bridge_witness.json`
- `projection_bundle.json`
- `model_output.json`
- `claim_gate_report.json`

P26 deliberately does not fabricate human labels or kappa. The manifest and
summary expose:

- `human_labels_required: true`
- `human_labels_present: false`
- `kappa_present: false`

## 7. Output Package

The output root contains:

- `run_manifest.json`
- `cases/`
- `pilot_summary.json`
- `pilot_summary.md`
- `claim_gate_report.json`
- `evidence_ledger.json`

The claim gate report is built through the existing P12/P13 gate path. P26 does
not create a parallel claim-gate system.

## 8. Claim Boundary

P26 outputs must preserve these boundaries:

- P26 defaults to dry-run.
- Controlled live pilot alone is not measurement validation.
- Live API success alone does not imply measurement validation.
- Human labels and kappa remain required in P27.
- Contamination audit and metric bridge freshness are required before
  `measurement_validated`.
- Engineering success is not scientific validation.
- Synthetic/proxy evidence does not certify deployed V-information
  submodularity.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.

## 9. Determinism

Dry-run and unit-test behavior is deterministic:

- no timestamps;
- no UUIDs;
- no randomness;
- no network calls;
- stable JSON serialization;
- stable Markdown output;
- stable case, condition, and reason-code ordering.

The same input should produce byte-identical JSON and Markdown outputs.

## 10. Next Phase

Recommended next phase:

```text
P27 Human Label and Kappa Artifact Protocol Implementation
```

P27 should add label/kappa artifact handling. It must not treat P26 live pilot
completion as measurement validation.
