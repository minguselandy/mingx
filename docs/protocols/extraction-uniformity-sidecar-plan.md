# Extraction-Uniformity Sidecar Plan

**Status:** sidecar plan  
**Layer:** extraction `M* -> M` bridge risk  
**Live API:** not authorized by this plan  
**Maximum claim:** extraction-audit evidence, not selector-regime validity


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

This sidecar measures whether extraction failures are approximately uniform across value strata. It addresses the paper's `M* -> M` bridge-risk layer and does not extend the weak-submodular guarantee from extracted candidate pool `M` back to upstream information space `M*`.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `vinfo_proxy_supported`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Key Quantities

```text
p_simple = fraction of simple findings
c_high = completeness for simple or high-capture findings
c_low = completeness for complex or low-capture findings
Delta_hat = c_low - c_high
c_effective = p_simple * c_high + (1 - p_simple) * c_low
```

Interpretation:

- if `Delta_hat` is near zero, extraction loss may be approximately uniform;
- if `Delta_hat` is strongly negative, complex/high-value content is disproportionately lost;
- either result is extraction-risk evidence, not selector-regime proof.

## 3. Required Preconditions

Do not run this as scientific evidence unless:

- contamination status is acceptable for measurement interpretation;
- annotation protocol is fixed;
- label reliability is known or explicitly bounded;
- source questions and derived sidecar artifacts are separated;
- candidate pools and extracted findings have stable ids.

## 4. Outcome Labels

| Condition | Interpretation |
|---|---|
| contamination failure | `pilot_only`; no scientific extraction conclusion |
| missing labels | design or dry-run only |
| missing reliability evidence | exploratory only |
| `c_low` materially below `c_high` | extraction non-uniformity risk |
| `c_low` near `c_high` with adequate power | uniformity not rejected, but not selector proof |

## 5. Outputs

```text
extraction_audit_manifest.json
extraction_labels.jsonl
stratum_completeness_report.json
extraction_uniformity_summary.md
claim_gate_report.md
```

## 6. Acceptance Criteria

The sidecar is accepted when it reports `c_high`, `c_low`, `Delta_hat`, confidence intervals or uncertainty bands, and a clear claim boundary.
