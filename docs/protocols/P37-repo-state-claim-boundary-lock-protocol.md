# P37 Repo-State and Claim-Boundary Lock Protocol

**Milestone:** P37  
**Status:** protocol specification  
**Live API:** prohibited  
**Primary output:** `docs/reviews/P37-repo-state-and-claim-boundary-lock-review.md`


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

P37 reconciles the current repository state, local branch state, paper framing, and evidence status before new experimental work begins. It prevents stale migration assumptions from controlling development after the public repository has advanced.

The output is a lock report, not a code feature.


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


## 2. Required Inputs

Inspect the following, if available:

- GitHub `main`
- local original repository: `C:\Users\Mingx\Documents\mx-codex\mingx`
- local development repository: `C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev`
- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/current-work-summary.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `configs/runs/README.md`

If a local path is unavailable, record it as unavailable rather than inferring status.

## 3. Preflight Commands

Run from the local original repo:

```bash
git status --short
git branch --show-current
git log --oneline -20
```

Then verify expected project files:

```bash
test -f docs/archive/context_projection_revised_v10.md
test -f docs/paper-alignment-v10.md
test -f docs/experiment-design-overview.md
test -f docs/protocols/phase-b-replay-protocol.md
test -f docs/phase-tree-crosswalk.md
test -d cps
```

On Windows PowerShell:

```powershell
git status --short
git branch --show-current
git log --oneline -20
Test-Path docs/archive/context_projection_revised_v10.md
Test-Path docs/paper-alignment-v10.md
Test-Path docs/experiment-design-overview.md
Test-Path docs/protocols/phase-b-replay-protocol.md
Test-Path docs/phase-tree-crosswalk.md
Test-Path cps
```

## 4. Unsafe-Claim Search

Search for unsafe or ambiguous claim language:

```bash
rg -n "measurement_validated|scientific validation|deployed V-information certification|certified greedy-valid|human labels|human-human kappa|kappa|Route B|model_adjudicated" docs cps tests README.md configs || true
```

Every occurrence must be classified as one of:

- safe boundary statement
- historical reference
- unsafe overclaim
- ambiguous wording needing rewrite

## 5. Required Report Sections

The P37 review report must include:

1. current branch;
2. commit range inspected;
3. whether there are tracked modifications;
4. whether untracked files are related or unrelated;
5. current paper source;
6. current repository-to-paper alignment;
7. implemented capabilities;
8. missing capabilities;
9. current live mini-batch interpretation;
10. contamination status;
11. human-label and kappa status;
12. Route B status, if files exist;
13. whether Phase B replay protocol exists;
14. recommended next milestone;
15. validation results.

## 6. Required Interpretations

The report must explicitly say:

- the current scaffold is a measurement/runtime-audit scaffold;
- `cps/` is the canonical package for new code;
- reduced-scope or contamination-failed live artifacts are not scientific validation;
- the current contamination-failed mini-batch remains `pilot_only`;
- no human labels or kappa may be fabricated;
- model-adjudicated labels are not human labels;
- Route B cannot claim `measurement_validated`.

## 7. Validation

Preferred:

```bash
uv run pytest -q
```

Fallback:

```bash
python -m pytest -q
```

If validation is skipped, record the exact reason.

## 8. Exit Criteria

P37 is complete when:

- the review report exists;
- unsafe claim occurrences are classified;
- local repo state is clean or unrelated changes are explicitly listed;
- current evidence status is unambiguous;
- the next milestone is recommended as P38/P39/P40 rather than live rerun by default.
