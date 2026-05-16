# P63R-FixA HotpotQA Support-Classification Positive Control

## Purpose

P63R-FixA is relabeled as a circular positive-control diagnostic. It is not independent metric bridge evidence.

The run is still useful as a sanity check: it proves the calibration machinery detects a perfectly aligned control when the utility is defined from the same measured quantity as the metric. It does not repair the failed HotpotQA answer-NLL bridge.

## Why This Is Circular

FixA used:

```text
delta_logloss = NLL(support_label | question + candidate_packet + context_L)
              - NLL(support_label | question + candidate_packet + context_L union A)

delta_utility = round(delta_logloss, 12)
```

Because `delta_utility` is the rounded `delta_logloss`, the perfect fit is tautological. The result is therefore:

```text
positive_control_only
circular_alignment_control
not_metric_bridge_evidence
```

## Inputs And Outputs

- Candidate pools: `artifacts/benchmarks/hotpotqa_candidate_pools.jsonl`
- Delta records: `artifacts/benchmarks/hotpotqa_support_classification_delta_records.jsonl`
- Operator rows: `artifacts/operator_inputs/p55_hotpotqa_support_classification_rows.jsonl`
- Calibration output: `artifacts/experiments/p55_hotpotqa_support_classification_bridge_calibration/`

No calibration was rerun for this relabel. The existing artifacts were relabeled to reflect the review finding.

## Diagnostic Metrics

- Delta records generated / validated: `643 / 643`
- Operator rows generated / validated: `643 / 643`
- Support-classification row instances: `643`
- Train rows: `450`
- Heldout rows: `193`
- Heldout fraction: `0.3001555209953344`
- Effective sample size: `643`
- `c_hat_s`: `1.0`
- `zeta_hat_s`: `0.0`
- Normalized residual: `0.0`
- Sign agreement: `1.0`
- Spearman rho: `1.0`

These metrics demonstrate only that the calibration code recognizes a circularly aligned positive control. They do not demonstrate a real bridge from an independent utility to a model log-loss metric.

## Relabeled Status

- Gate result: `positive_control_only`
- Metric claim level: `positive_control_only`
- Claim status: `positive_control_only; circular_alignment_control; not_metric_bridge_evidence; no_claim_upgrade`

## Claim Boundary

- FixA cannot support `calibrated_proxy_supported`.
- FixA cannot support `vinfo_proxy_supported`.
- FixA cannot support measurement validation.
- FixA cannot support paper evidence.
- FixA cannot support P56 unblock.
- P56/P65/P66 were not started.
- The previous failed answer-NLL bridge remains the current negative bridge result for the non-circular HotpotQA design.

## Next Step

Treat FixA as a diagnostic sanity check only. The next bridge attempt must use a non-circular utility that is independently defined from the measured log-loss.
