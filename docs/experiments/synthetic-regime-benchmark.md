# Synthetic Regime Benchmark

## Purpose

This benchmark is an offline structural diagnostic for CPS projection artifacts. It creates deterministic synthetic set-function instances where the expected selector behavior is known in advance, then checks whether the diagnostics separate redundancy-dominated, pairwise-synergy, and higher-order-synergy regimes.

The benchmark is engineering evidence for diagnostic plumbing and replayability only. It is not Phase 1 scientific closure and does not replace the deferred P04 operator workflow.

## Non-goals

- No live API calls or model-provider calls.
- No human annotation, kappa, contamination, or bridge validation.
- No certification of deployed V-information weak submodularity.
- No `measurement_validated` claim.
- No required OR-Tools, submodlib, LangGraph, Graphiti, LangExtract, or Langfuse dependency.

## Synthetic Families

### Redundancy-Dominated

Items are grouped into near-duplicate clusters. The first selected item in a cluster contributes most of the value, and additional items from the same cluster contribute only a residual value.

Expected signature:

- high block-ratio LCB
- low pairwise synergy mass
- small greedy-vs-oracle or greedy-vs-augmented gap
- selector label may be `greedy_supported`
- selector action may be `monitored_greedy`

### Pairwise-Synergy

Items have singleton value plus sparse pairwise interaction bonuses. Each item has bounded complementarity degree, so pairwise diagnostics should detect positive interaction mass.

Expected signature:

- pairwise interaction mass detected
- lower pair/block ratio than redundancy-dominated instances
- seeded or augmented greedy may improve over vanilla greedy
- selector label should be `pairwise_escalate` or remain `ambiguous`, not silently claim deployed behavior

### Higher-Order-Synergy / Prerequisite

Sparse triples or prerequisite chains receive bonuses that are not fully explained by singleton or pairwise terms. Pairwise-only diagnostics may be insufficient.

Expected signature:

- positive triple-excess or block-3 diagnostic signal
- higher-order ambiguity flag may fire
- `greedy_supported` must be withheld when triple excess is high
- selector action should escalate to interaction-aware search or mark the case ambiguous

## Outputs

The benchmark writes deterministic, replayable audit files:

- `events.jsonl`
- `candidate_pools.jsonl`
- `projection_plans.jsonl`
- `budget_witnesses.jsonl`
- `materialized_contexts.jsonl`
- `metric_bridge_witnesses.jsonl`
- `diagnostics.jsonl`
- `projection_bundles.jsonl`
- `summary.json`
- `report.md`

`projection_bundles.jsonl` contains `ProjectionBundleV1` rows with stable canonical hashes. The event log also includes `projection_bundle_materialized` events.

## Pass/Fail Interpretation

| Condition | Expected interpretation |
|---|---|
| Redundancy has high block-ratio, low synergy, and small greedy gap | synthetic `greedy_supported` path is behaving as expected |
| Pairwise regime has positive interaction mass | pairwise escalation signal is detected |
| Pairwise seeded/augmented greedy improves over vanilla greedy | escalation path is structurally useful in this synthetic regime |
| Higher-order regime has positive triple excess | pairwise-only support is insufficient |
| Higher-order regime is labeled `greedy_supported` despite triple excess | benchmark failure |
| Metric claim level is legacy `Vinfo_proxy_certified` or `measurement_validated` | benchmark failure |
| Projection bundle hash changes across identical seed/config reruns | determinism failure |

## Claim Boundary

Allowed metric claim levels are `vinfo_proxy_supported`, `operational_utility_only`, and `ambiguous_metric`. The benchmark must never emit legacy `Vinfo_proxy_certified` or `measurement_validated`.

Synthetic benchmark success does not certify deployed V-information weak submodularity. P04 remains the required scientific closure path for live follow-up, contamination review, human labels, kappa, bridge evidence, and human confirmation.
