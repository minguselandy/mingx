# P44 Manuscript Evidence Integration Plan

**Milestone:** P44
**Status:** no-git DEV manuscript integration completed
**Live API:** prohibited
**Primary target:** `docs/archive/context_projection_revised_v10.md`


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from `git status`, run plans, `run_summary.json`, `events.jsonl`, and concrete artifacts. Paper text and roadmap documents are not run-completion evidence.


## 1. Purpose

P44 integrates new evidence from P38-P43 into the revised v10 manuscript without claim inflation. The manuscript should continue to read as conditional theory + bridge statement + proxy-regime certification + runtime-audit evidence, not as deployed scientific validation.

## P44 No-Git Automation Result

- Execution time: `2026-05-05T02:03:32.2550785+08:00`
- Mode: no-git direct development in `mingx-dev`
- Manuscript target updated: `docs/archive/context_projection_revised_v10.md`
- Review target updated: `docs/reviews/P44-manuscript-evidence-integration-review.md`
- Evidence integrated: P41 Route B model-adjudicated pilot packaging, P42 reduced-scope live-smoke gate result, and P43 deterministic realistic-task benchmark scaffold
- Claim ceiling: `model_adjudicated_pilot_only`, `pilot_only`, or `operational_utility_only`, depending on evidence surface
- Live API: skipped; P44 is manuscript/doc integration only
- Claim boundary: no human labels, kappa, contamination pass, fresh metric bridge, `measurement_validated`, scientific validation, or deployed V-information certification is claimed
- Validation: `python -m compileall cps scripts` passed; focused manuscript/framing tests passed with `31 passed`; full `uv run pytest -q` passed with `435 passed, 4 skipped`
- Risky claim scan: safe; occurrences are denied claims, boundary conditions, claim-gate rules, future/conditional targets, explicit non-claims, Route B ceilings, or pilot ceilings


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `structural_synthetic_only`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Evidence Sources Eligible for Integration

Candidate sources:

| Source | Eligible manuscript use | Maximum claim |
|---|---|---|
| P38 synthetic benchmark | structural validity floor for diagnostics | `structural_synthetic_only` |
| P39 schema freeze | artifact stability / replay readiness | engineering / replay readiness |
| P40 Phase B replay | observability and diagnostic recomputation evidence | replay evidence only |
| P41 Route B | model-adjudicated operational pilot evidence | `model_adjudicated_pilot_only` / `operational_utility_only` |
| P42 follow-up live batch | reduced-scope pilot evidence, if cleanly executed | pilot evidence; not measurement validation alone |
| P43 Phase C benchmark | realistic-task projection behavior under explicit bridge scope | operational or calibrated proxy evidence |
| extraction-uniformity sidecar | `M* -> M` bridge-risk discussion, if executed | extraction audit evidence |

## 3. Proposed Manuscript Insertions

### 3.1 Abstract

Only update if evidence materially changes current evidence status. Avoid saying validation is complete unless full validation gates are met.

### 3.2 Section 4.3.1 Synthetic benchmark

Add a concise results table:

| Family | Expected signature | Observed result | Claim level |
|---|---|---|---|
| redundancy-dominated | high block-ratio, low synergy | TBD | `structural_synthetic_only` |
| pairwise-synergy | interaction mass, seeded greedy improves | TBD | `structural_synthetic_only` |
| higher-order | triple-excess / ambiguity; no greedy-valid false positive | TBD | `structural_synthetic_only` |

### 3.3 Section 6 Runtime artifacts

Add a compact artifact schema and replay-status table if P39/P40 are complete.

### 3.4 Evidence status paragraph

Add an explicit evidence ladder summary:

```text
The current evidence package supports deterministic artifact generation, structural synthetic diagnostics, and offline replay recomputation where replay fields are present. It does not supply human labels, human-human kappa, contamination closure, or a fresh deployed metric bridge sufficient for measurement validation.
```

### 3.5 Limitations

Update limitations to include:

- replay limitations;
- Route B non-human-label boundary;
- contamination status of any live pilot;
- metric bridge limitations;
- missing human labels/kappa if still absent.

## 4. Required Tables

Suggested manuscript-facing tables:

1. Evidence Ladder Table
2. Conservative Claim Gate Table
3. Replay Usability Table
4. Route B Label Boundary Table
5. Metric Bridge Scope Table
6. Optional Realistic-Task Benchmark Summary Table

## 5. Unsafe Wording Ban List

Do not add:

```text
measurement_validated
scientifically validated
certified deployed V-information submodularity
theorem-backed heuristic pipeline
validated scheduler
full multi-agent runtime verification
human labels, unless actual human labels exist
human-human kappa, unless actual kappa exists
```

Allowed language:

```text
structural synthetic evidence
runtime-audit evidence
replayable artifact evidence
model-adjudicated pilot evidence
operational-utility-only diagnostic
calibrated proxy evidence, when bridge is fresh
ambiguous, when bridge or evidence is insufficient
```

## 6. Review Requirements

Before merging manuscript changes:

```bash
rg -n "measurement_validated|scientific validation|certified deployed|theorem inheritance|human-human kappa|human labels" docs/archive/context_projection_revised_v10.md docs/paper docs/reviews
```

Every occurrence must be intentionally bounded.

## 7. Acceptance Criteria

P44 is accepted when:

- manuscript changes are traceable to evidence artifacts;
- claim-level tables match claim gate outputs;
- limitations remain explicit;
- Route B is not presented as Route A;
- no artifact completeness is treated as scientific validation;
- final review verdict is `ACCEPT_FOR_SUPERVISOR_REVIEW` or stricter.
