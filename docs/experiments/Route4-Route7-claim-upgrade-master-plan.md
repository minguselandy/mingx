# Route 4-7 Claim-upgrade Master Plan

Status: P70V protocol freeze
Claim status: `no_claim_upgrade`

This package freezes the validation-grade development program after the Route 2
and Route 3 negative results. It does not run experiments, create operator
inputs, call live APIs, modify manuscript claims, or upgrade claims. All target
claims below are future-gated until the relevant route runs, passes its
predeclared gates, and receives independent review.

## Current Evidence Boundary

Route 2 produced accepted HotpotQA operational replay and comparison evidence.
It showed that the v12 diagnostic policy improved supporting-fact recall
against deployable baselines under matched budgets, but the Route 2 bridge gates
failed closed. Route 2 therefore remains `operational_utility_only`.

Route 3 tested support-grounded bridge revisions. Route 3A failed closed below
the minimum validated-row gate. Route 3B reached calibration scale and passed
non-circularity checks, but failed the preregistered sign-agreement, Spearman,
and normalized-residual gates. Route 3 remains `no_claim_upgrade`.

## Claim Ladder

| Level | Route dependency | Review state | Current status |
|---|---|---|---|
| `operational_utility_only` | accepted operational replay/comparison | accepted for Route 2 | current ceiling for existing evidence |
| `metric_bridge_support_candidate` | Route 4 bridge rows and gates | future review required | not achieved |
| `calibrated_proxy_supported_candidate` | Route 4 calibration plus bridge witness | future review required | not achieved |
| `calibrated_proxy_supported` | accepted candidate package and paper-level review | future review required | denied for current evidence |
| `vinfo_proxy_supported_candidate` | Route 5 fixed deployed-model/log-loss proxy package | future review required | not achieved |
| `vinfo_proxy_supported` | accepted scoped fixed-model/log-loss package | future review required | denied for current evidence |
| `measurement_validation_candidate` | Route 6 hybrid validation gates | future review required | not achieved |
| measurement validation evidence | accepted Route 6 human/hybrid validation package | future review required | denied for current evidence |
| scoped multi-benchmark selector superiority | Route 7 finite benchmark matrix plus dependencies | future review required | denied for current evidence |

Literal global selector superiority is not a valid target claim. Route 7 may
only pursue scoped multi-benchmark selector superiority over a finite declared
experimental distribution.

## Route Dependency Graph

Route 4 is the strict dependency for any future metric-bridge or calibrated
proxy claim. Route 5 can be designed in parallel, but its verification must bind
to Route 4-compatible rows and a fixed deployed-model/log-loss proxy. Route 6
can prepare rubric, annotation, contamination, and model-bias audits in
parallel, but measurement validation evidence requires completed human or
hybrid validation. Route 7 can prepare benchmark and baseline registries in
parallel, but any scoped superiority claim must respect the Route 4/5/6 claim
ceiling required by the paper use case.

## Execution Order

1. Route 4: redesign the bridge target and generate reviewed candidate bridge
   evidence only after pre-registration.
2. Route 5: verify a scoped fixed deployed-model/log-loss proxy after Route 4
   rows exist.
3. Route 6: run external measurement validation once labels, rubric,
   contamination audit, and adjudication resources are approved.
4. Route 7: run finite multi-benchmark selector comparisons with scoped
   statistical gates.

Parallel preparation is allowed for Route 5 evaluator specification, Route 6
rubric design, and Route 7 baseline registry work. Evidence generation remains
route-gated.

## Review Gates

Every route requires:

- pre-registration before row or trace generation;
- source-data provenance and contamination review;
- row-key or trace-key stability checks;
- negative controls and appropriate positive controls;
- deterministic reports with no timestamps, UUIDs, raw API dumps, or secrets;
- independent review before any candidate claim is promoted.

Stop if any route detects circular utility, missing real data, unavailable
approved evaluators, unstable row identity, failed contamination gates,
unrecoverable annotation quality, or unsafe claim wording.

Continue only when the route-specific plan is accepted, required inputs exist,
storage policy is approved, and all pre-score gates are satisfied.

Escalate if human annotation, live API spend, external artifact storage, or a
candidate claim promotion is proposed.

## Route Summaries

Route 4 freezes a non-circular metric bridge redesign over FEVER and HotpotQA
first strata. It can at most produce a metric bridge support candidate or a
calibrated proxy candidate pending independent review.

Route 5 freezes fixed deployed-model/log-loss proxy verification. It separates
formal V-information from a scoped fixed-model proxy and can at most produce a
future `vinfo_proxy_supported_candidate` for that proxy protocol.

Route 6 freezes external measurement validation. It requires human sentinel or
hybrid annotation, agreement metrics, contamination audit, and model-bias audit
before measurement validation evidence can be considered.

Route 7 freezes scoped multi-benchmark selector-superiority testing. It rejects
literal global selector superiority and may only claim a scoped result over a
finite benchmark/task/budget distribution after gates and review.

## Artifact Policy

Commit protocol documents, compact JSON readiness reports, schemas, manifests,
checksums, and validation summaries. Do not commit raw live API responses,
external dataset mirrors, large JSONL rows, operator inputs, or raw dispatch
traces unless a future package explicitly approves release assets, Git LFS, DVC,
or external artifact storage.

## Denied Active Claims

Current evidence does not support:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- paper-grade evidence
- metric bridge support
- fixed deployed-model/log-loss proxy verification
- scoped multi-benchmark selector superiority
- global selector superiority
- deployed V-information verification
