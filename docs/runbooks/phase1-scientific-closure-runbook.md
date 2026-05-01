# Phase 1 Scientific Closure Runbook

## Purpose

This runbook guides operator-controlled P04 execution for Phase 1 scientific closure. It covers fresh follow-up package generation, reduced-scope live follow-up execution, contamination gate inspection, human annotation, kappa evaluation, bridge evaluation, and the final claim-level decision.

This is an operator runbook only. It does not authorize Codex or automation to run live APIs, fill annotation labels, compute kappa from fabricated labels, validate bridge claims without evidence, or claim `measurement_validated`.

## Non-negotiable claim gates

- contamination failure => `pilot_only`.
- missing human labels => `not measurement_validated`.
- missing kappa => `not measurement_validated`.
- stale or missing metric bridge => `operational_utility_only` or ambiguous.
- engineering success does not imply scientific validation.
- no `measurement_validated` claim is allowed without all required evidence.

## Required preconditions

- Working tree is clean enough for operator execution, or the current dirty baseline is explicitly accepted and recorded before running live commands.
- API profile is configured from the approved profile, currently `dashscope-qwen-phase1`.
- Live model and logprob readiness have been checked by the operator.
- Source plan path exists.
- Replacement manifest path exists.
- Operator decision sheet exists and is fully signed. Pending placeholders are not acceptable.
- Follow-up package is generated from the signed decision sheet.
- Annotation templates are available before label collection begins.
- No unreviewed changes exist in scientific gate code, including contamination, annotation, reliability/kappa, bridge, cohort status, or measurement status logic.

Current known reduced-scope source paths:

- Source plan: `artifacts/phase1/live_mini_batch_plan.json`
- Replacement manifest: `artifacts/phase1/live_mini_batch/replacement_manifest.json`
- Pending decision sheet: `artifacts/phase1/live_mini_batch/exports/contamination_operator_decision_sheet.md`
- Follow-up output root: `artifacts/phase1/live_mini_batch_followup`

The current decision sheet contains pending fields. It must be copied or updated into an approved operator decision sheet before Step B is run.

Project runtime note: API, follow-up, and cohort commands below must be run from the approved project Python environment with project dependencies available. Do not install dependencies automatically during P04; resolve environment readiness as an operator precondition.

## Step A: Engineering preflight

Run these local checks before any operator-run live step:

```powershell
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
python -m compileall cps scripts
pytest tests/test_phase1_followup.py -q
pytest tests/test_phase1_contamination.py -q
pytest tests/test_phase1_bridge.py -q
pytest tests/test_phase1_annotation.py -q
```

Check API profile export without making a live request:

```powershell
python -m api --export-phase1-env --profile dashscope-qwen-phase1
```

The following commands call live provider APIs. They are OPERATOR-RUN ONLY:

```powershell
python -m api --probe-phase1-logprobs --env .env --model-role small
python -m api --probe-phase1-logprobs --env .env --model-role frontier
python -m scripts.list_phase1_usable_models --env .env --timeout 15 --json-out artifacts/phase1/model_probe/usable_models.json --markdown-out docs/phase1-usable-models.md
```

Do not start live follow-up if either model-role probe fails, returns degenerate all-zero token logprobs, or does not satisfy the Phase 1 request contract.

## Step B: Build fresh follow-up package

Use the P03 follow-up CLI with a signed operator decision sheet:

```powershell
python -m cps.runtime.followup --source-plan artifacts/phase1/live_mini_batch_plan.json --replacement-manifest artifacts/phase1/live_mini_batch/replacement_manifest.json --decision-sheet <APPROVED_DECISION_SHEET> --output-root artifacts/phase1/live_mini_batch_followup
```

Expected outputs under `<OUTPUT_ROOT>`:

- `followup_plan.json`
- `calibration_manifest.json`
- `blocked_questions.json`
- `lineage.json`
- `README.md`
- storage roots for cache, measurements, checkpoints, and exports

Failure conditions:

- decision sheet still contains `[pending]`
- decision sheet run id does not match the source run summary
- approved follow-up action is not `replace_only`
- question decisions do not match the drop list
- replacement manifest seed, source manifest hash, source dataset hash, selection algorithm, replacement policy, or per-hop counts do not match the source plan
- generated follow-up calibration differs from the replacement manifest
- output root is inside a protected source run path

If the CLI returns nonzero, stop and do not run Step C.

## Step C: Run reduced-scope live follow-up

OPERATOR-RUN ONLY.

After Step B succeeds and the operator confirms API readiness, run the generated follow-up plan through the normal cohort entry point:

```powershell
python -m cps.runtime.cohort --plan artifacts/phase1/live_mini_batch_followup/followup_plan.json --backend live --env .env
```

This command may call live provider APIs. It must not be run by automation.

Expected live follow-up outputs are produced under the follow-up plan storage roots, especially:

- `exports/run_summary.json`
- `exports/contamination_diagnostics.json`
- `exports/bridge_diagnostics.json`
- `exports/annotations/annotation_manifest.json`
- `exports/annotations/labels/primary_a.csv`
- `exports/annotations/labels/primary_b.csv`
- `exports/annotations/labels/expert.csv`
- measurement `events.jsonl`

Treat the CLI report and `exports/run_summary.json` as the run-level source of truth. Inspect `pipeline_status`, `measurement_status`, contamination status, annotation status, kappa status, and bridge status.

## Step D: Inspect contamination gate

Inspect the follow-up run contamination diagnostics:

```powershell
Get-Content artifacts/phase1/live_mini_batch_followup/exports/contamination_diagnostics.json
Get-Content artifacts/phase1/live_mini_batch_followup/exports/run_summary.json
```

If contamination `gate_decision` is `fail`:

- stop scientific interpretation
- report `pilot_only`
- do not proceed to `measurement_validated`
- preserve `contamination_diagnostics.json`, `contamination_escalation_bundle.json`, `events.jsonl`, and `run_summary.json` for audit
- create a new operator decision packet before any rerun or remediation

Contamination failure is a scientific stop, not an engineering retry signal.

## Step E: Human annotation

Expected annotation files:

- `exports/annotations/annotation_manifest.json`
- `exports/annotations/labels/primary_a.csv`
- `exports/annotations/labels/primary_b.csv`
- `exports/annotations/labels/expert.csv`, if required by the annotation manifest

Codex must not fabricate labels.

Before ingestion, inspect annotation status:

```powershell
python -m cps.runtime.annotation --annotation-manifest <ANNOTATION_MANIFEST>
```

The command below is test-only and forbidden for scientific closure:

```powershell
python -m cps.runtime.annotation --annotation-manifest <ANNOTATION_MANIFEST> --fill-synthetic-passthrough
```

Use real human labels only. If human labels are missing, keep the run at `not measurement_validated` and do not proceed to a validation claim.

## Step F: Kappa and bridge evaluation

The existing repository path computes bridge artifacts, materializes annotation artifacts, ingests completed human labels, computes kappa, and finalizes the variance/bias budget through the cohort runner.

After real labels are complete, rerun the same follow-up cohort plan so the existing cohort path can ingest annotation labels and compute reliability:

```powershell
python -m cps.runtime.cohort --plan artifacts/phase1/live_mini_batch_followup/followup_plan.json --backend live --env .env
```

OPERATOR-RUN ONLY.

After rerun, inspect:

- `exports/run_summary.json`
- `exports/annotations/annotation_status.json`
- kappa summary path recorded in `run_summary.json`
- `exports/bridge_diagnostics.json`
- `exports/variance_bias_budget.json`

Direct standalone kappa and bridge evaluation CLIs were not safely discoverable. If a future operator wants direct one-shot commands, add them in a separate reviewed engineering phase rather than inventing commands here.

## Step G: Claim-level decision table

| Condition | Status |
| --- | --- |
| contamination fail | `pilot_only` |
| contamination pass + missing labels | `pilot_only` / `annotation_required` |
| labels complete + missing kappa | `pilot_only` / `kappa_required` |
| kappa unacceptable | `pilot_degraded` or ambiguous |
| bridge missing/stale | `operational_utility_only` or ambiguous |
| contamination pass + labels complete + kappa acceptable + bridge pass | `measurement_validated` candidate, requires human confirmation |

`measurement_validated` is never automatic. It requires human confirmation after reviewing the actual artifacts.

## Step H: Required final review

P04 review must remain `BLOCKED_OPERATOR_REQUIRED` until real artifacts exist and a human operator has reviewed them.

Do not auto-advance to P05.

Do not mark P04 `ACCEPT` based on this runbook alone.

The final P04 evidence review must include:

- exact live commands run by the operator
- follow-up package paths
- run summary path
- contamination diagnostics path and gate decision
- annotation manifest and completed label paths
- kappa summary path and acceptability decision
- bridge diagnostics path and freshness decision
- final claim-level status
- explicit confirmation that no scientific claim was upgraded without evidence
