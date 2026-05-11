# Diagnostic Threshold Contract V12

Status: P53 protocol scaffold
Framing: Proxy-Regime Diagnosis
Primary anchors: `docs/archive/context_projection_fixed_v12.md`, `docs/paper-alignment-v12.md`

## 1. Purpose

The diagnostic threshold contract is a pre-registration / audit artifact. It records the stratum, metric-bridge state, thresholds, lower-confidence-bound method, effective-sample-size gate, drift handling, and fail-closed rules that must be reviewed before a Section 4 diagnostic label is emitted.

It is not bridge evidence. It is not validation. It does not by itself authorize `vinfo_proxy_supported` or `calibrated_proxy_supported`. It does not convert synthetic, fixture, or replay-completeness evidence into paper-grade evidence.

The contract exists to make every diagnostic label traceable to one of two sources:

1. predeclared thresholds and methods; or
2. explicit fail-closed rules.

No missing threshold may be interpreted post hoc.

## 2. Scope

The contract applies to dispatch-time selector diagnostics over a declared active stratum. It covers metric-claim downgrades and selector-regime labels. It does not create a new bridge-calibration result, run live APIs, create human labels, establish human-human kappa, validate a metric bridge, or verify deployed V-information behavior.

The current P45 `bio_attribute` stratum remains non-calibrated, fail-closed, not bridge support, and not `calibrated_proxy_supported`.

## 3. Active Vocabulary

Allowed `metric_claim_level` values:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

Allowed `selector_regime_label` values:

- `greedy_supported`
- `pairwise_escalate`
- `higher_order_risk`
- `ambiguous`

Deprecated labels may appear only as denied, legacy, or archive examples:

- `Vinfo_proxy_certified`
- `greedy_valid`
- `measurement_validated`

## 4. Required Contract Fields

Each contract instance must include these top-level fields:

| Field | Requirement |
|---|---|
| `contract_id` | Stable contract identifier. |
| `contract_schema_version` | Explicit template/schema version. |
| `calibration_epoch` | Bridge or diagnostic epoch that the thresholds are bound to. |
| `active_stratum` | Exact stratum that may use the thresholds. |
| `metric_claim_level_precondition` | Metric-claim level and bridge conditions required before selector labeling. |
| `block_size_max` | Maximum evaluated block size. |
| `signal_threshold` | Numeric activity threshold, or inactive with fail-closed behavior. |
| `ratio_lcb_method` | Lower-confidence-bound method or conservative fallback. |
| `ratio_quantile` | Lower quantile used for block-ratio reporting. |
| `ratio_lcb_threshold` | Healthy pair-block-ratio threshold. |
| `pairwise_excess_threshold` | Positive pairwise interaction threshold. |
| `sag_gap_threshold` | Meaningful seeded-augmented-greedy gap threshold. |
| `triple_excess_threshold` | Triple or hidden-synergy sentinel threshold. |
| `min_effective_sample_size` | Minimum ESS before non-ambiguous diagnostic labels are allowed. |
| `drift_policy` | Fresh, stale, ambiguous, missing, and mismatched bridge handling. |
| `underpowered_policy` | Required downgrade below ESS or denominator gates. |
| `fixture_policy` | Fixture-only evidence restrictions. |
| `synthetic_policy` | Synthetic-only evidence restrictions. |
| `decision_logic` | Deterministic label rules and precedence. |
| `claim_boundary` | Denied claims and maximum claim ceiling. |
| `paper_evidence_policy` | Paper-evidence eligibility rules. |

The `active_stratum` object must include, at minimum:

- `task_family`
- `model_tier`
- `materialization_policy`
- `block_size`
- `candidate_slice`
- `metric`
- `data_source_kind`

## 5. Threshold Policy

Universal scientific thresholds are not assumed. Thresholds are stratum-specific unless separately justified in a review note.

All threshold values must be one of:

1. explicit numeric thresholds; or
2. explicitly inactive gates with fail-closed behavior.

Threshold values may be `null` only when the gate is inactive and the decision fails closed. A missing threshold cannot be filled after observing results. If a contract omits a required threshold or leaves it ambiguous, selector-regime output must fall to `ambiguous` and metric-claim output must remain `ambiguous_metric` or `operational_utility_only`.

## 6. MetricBridgeWitness Semantics

`MetricBridgeWitness` records bridge status and provenance. `MetricBridgeWitness` presence is not automatically bridge support.

A stale, missing, mismatched, underpowered, incomplete, or failed witness must downgrade claims. Replay usability does not imply metric support.

The contract must not infer a metric bridge from:

- replay completeness;
- synthetic structural signatures;
- fixture realistic-task success;
- extraction audit completeness;
- `ReprojectionWitness` improvement rows;
- model-adjudicated labels.

Bridge-qualified metric claims require exact active-stratum match, fresh status, sufficient ESS, complete provenance, and a phase-specific review that the witness supports the declared metric claim. The contract alone never supplies that evidence.

## 7. Drift Policy

The `drift_policy` must distinguish these statuses:

| Drift status | Required behavior |
|---|---|
| `fresh` | May proceed to threshold review only if active stratum, data source, ESS, and provenance match. |
| `stale` | Fail closed to `ambiguous_metric` or `operational_utility_only`; do not emit bridge-qualified claims. |
| `ambiguous` | Fail closed to `ambiguous_metric` and `ambiguous` selector label unless a stricter operational-only rule applies. |
| `missing` | Fail closed to `ambiguous_metric`; no bridge-qualified claim. |
| `mismatched` | Fail closed to `ambiguous_metric`; no claim inheritance across strata. |

## 8. Fixture and Synthetic Policies

Fixture-only evidence remains paper-ineligible. Fixture-only evidence cannot emit `vinfo_proxy_supported`. Fixture-only evidence cannot emit `calibrated_proxy_supported`.

Synthetic-only evidence remains structural-only. Synthetic-only evidence cannot emit `vinfo_proxy_supported`. Synthetic-only evidence cannot emit `calibrated_proxy_supported`.

These restrictions apply before selector-label thresholds are considered.

## 9. Decision Logic

The contract decision surface must be deterministic:

```text
if metric bridge missing/stale/underpowered/mismatched:
    metric_claim_level = operational_utility_only or ambiguous_metric
    no vinfo_proxy_supported claim
    no calibrated_proxy_supported claim

if signal denominator below threshold:
    selector_regime_label = ambiguous

if pair ratio healthy and pair excess low and SAG gap small:
    selector_regime_label = greedy_supported

if pair excess high and SAG gap meaningful:
    selector_regime_label = pairwise_escalate

if triple sentinel fires or hidden-synergy conflict appears:
    selector_regime_label = higher_order_risk

if signals conflict or sample is underpowered:
    selector_regime_label = ambiguous
```

Required precedence:

1. hard claim-boundary failures;
2. missing, stale, mismatched, or underpowered metric bridge;
3. fixture-only or synthetic-only evidence restrictions;
4. signal denominator and ESS checks;
5. triple or higher-order risk checks;
6. pairwise-escalation checks;
7. greedy-supported checks;
8. ambiguous fallback.

An earlier fail-closed condition blocks upgraded labels from later checks.

## 10. Label Traceability

Every emitted label must record which condition fired:

| Output | Required trace |
|---|---|
| `greedy_supported` | Numeric pair ratio, pairwise excess, SAG gap, signal denominator, ESS, and bridge precondition all passed. |
| `pairwise_escalate` | Pairwise excess and SAG gap thresholds fired after higher-precedence fail-closed rules passed. |
| `higher_order_risk` | Triple sentinel or hidden-synergy conflict fired after hard claim-boundary checks. |
| `ambiguous` | Signal, ESS, bridge, provenance, conflict, inactive gate, or threshold incompleteness caused fail-closed output. |
| `vinfo_proxy_supported` | Requires separate fresh fixed-model-to-`V_i` bridge, near-optimality argument, or empirical minimization evidence; this contract alone cannot grant it. |
| `calibrated_proxy_supported` | Requires a separate fresh utility-to-logloss bridge for the exact active stratum; this contract alone cannot grant it. |
| `operational_utility_only` | Utility diagnostics may be operationally useful but are not V-information support. |
| `ambiguous_metric` | Bridge missing, stale, failed, underpowered, mismatched, synthetic-only, fixture-only, or insufficiently specified. |

## 11. Review Rules

A reviewer must verify:

- active stratum is complete and matches the evidence source;
- calibration epoch is recorded;
- thresholds are numeric or explicitly inactive with fail-closed behavior;
- `ratio_lcb_method` and fallback are predeclared;
- `min_effective_sample_size` and signal denominator gates are present;
- drift policy includes `fresh`, `stale`, `ambiguous`, `missing`, and `mismatched`;
- underpowered policy fails closed to `ambiguous`, `ambiguous_metric`, or `operational_utility_only`;
- fixture-only and synthetic-only restrictions block upgraded metric claims;
- `MetricBridgeWitness` status is treated as a gate, not as support by mere presence;
- no label is upgraded by replay completeness, extraction audit completeness, `ReprojectionWitness` rows, or model-adjudicated labels.

## 12. Claim Boundaries

This protocol does not claim:

- measurement validation;
- deployed V-information verification;
- theorem-level deployed submodularity verification;
- synthetic evidence as bridge evidence;
- fixture evidence as paper-grade evidence;
- replay usability as metric support;
- extraction audit as selector validity;
- `ReprojectionWitness` as deployed runtime improvement;
- current P45 `bio_attribute` stratum as `calibrated_proxy_supported`;
- human-label validation;
- human-human kappa;
- deployed runtime improvement.

The maximum claim for P53 itself is `none`. P53 is a protocol scaffold only.

## 13. Template

The deterministic JSON template is:

- `docs/templates/diagnostic-threshold-contract-template.json`

The template is intentionally machine-neutral: no timestamps, UUIDs, absolute local paths, secrets, or run-specific identifiers. A concrete phase may copy it into a run-specific configuration only after assigning a reviewed active stratum and preserving the fail-closed rules.
