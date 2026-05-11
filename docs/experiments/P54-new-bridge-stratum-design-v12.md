# P54 New Bridge Stratum Design V12

## 1. Status and Claim Ceiling

Status: design/protocol scaffold only.

Claim ceiling:

- `metric_claim_level_max: none`
- `selector_regime_label_max: none`
- `paper_evidence_eligible: false`

P54 does not execute a bridge pilot, import rows, generate rows, run live APIs, validate a metric bridge, or upgrade any evidence claim. P55 remains blocked until this design receives independent review acceptance and the operator approves the selected data source.

## 2. Why P54 Exists After P45 Negative Closure

P45 implemented the bridge-calibration lane for the current `bio_attribute` stratum, but that stratum did not establish stable utility-to-logloss support. The preserved P45 result is fail-closed negative claim-gate evidence, not bridge support.

P54 exists because future bridge work must use either a materially new active stratum or a materially new fixed-logloss/utility design. It does not treat P45 as successful and does not claim that the P45 failure has been solved.

## 3. Chosen Stratum and Rejected Alternatives

Chosen stratum:

```text
evidence_packet_selection_microtask_v1
```

Task: select a small set of findings needed to answer a constrained factual/evidence question.

Target: forced-choice or exact-field answer with explicit target evidence.

Rationale: this option has the cleanest constrained target, the clearest fixed-model logloss path, and the least dependence on subjective claim-boundary classification. It can remain a dispatch-time worker projection task if the candidate pool, selected block identity, materialization policy, dispatch identity, and candidate-pool hash are fixed.

Rejected alternatives:

- `repo_change_review_microtask_v1`: useful for repo-claim guardrails, but it risks overfitting to repository-specific policy language and subjective violation taxonomy.
- `paper_revision_claim_gate_microtask_v1`: directly paper-facing, but it risks testing claim-boundary classification rather than context projection value unless candidate findings are designed with unusual care.

## 4. Material Distinction From P45 `bio_attribute`

P45 `bio_attribute` involved a closed/current stratum that failed to establish stable utility-to-logloss support. P54 is materially different:

- task family changes from `bio_attribute` extraction/adjudication to `evidence_packet_selection_microtask_v1`;
- target type changes to constrained forced-choice or exact-field answer evidence;
- utility is defined as decomposable answer correctness over declared fields, not the same `bio_attribute` utility target;
- logloss measurement requires explicit target evidence and target tokenization for the forced-choice/exact-field answer;
- candidate pools are evidence packets with distractors, prerequisites, qualifiers, and source conflicts, not attribute packets from the closed P45 stratum;
- P54 proposes a new stratum for future review only and does not reuse or scale the failed P45 canaries.

## 5. Task Family

```text
task_family = evidence_packet_selection_microtask_v1
```

The worker receives a constrained question and a fixed candidate pool of evidence packets. The projection decision selects a block of one or two packets to include in the worker context. The target is a declared answer field that can be scored by fixed-model logloss and by a decomposable utility metric.

## 6. Target Type

Target type:

```text
forced_choice_or_exact_field
```

Allowed target shapes:

- forced-choice answer from a fixed option set;
- exact short field such as an entity, status, version, date, or bounded category.

Open-ended free text is out of scope for the first P55 pilot unless a later review supplies a deterministic logloss and utility path.

## 7. Model Tier

Model tier:

```text
fixed_evaluated_model_tier
```

P55 must bind the evaluated model tier before importing or generating rows. Claim inheritance is forbidden across model tiers.

## 8. Materialization Policy

Materialization policy:

```text
fixed_order_evidence_packet_v1
```

Required properties:

- stable packet order inside each selected block;
- fixed packet header fields;
- fixed question and answer-option formatting;
- no prompt rewriting between logloss and utility measurements;
- materialized-context hash recorded for each row.

## 9. Decoding Policy

Decoding policy:

```text
deterministic_logloss_scoring_no_generation
```

The primary logloss path scores the declared target under fixed context. If any generated utility judgment is used in P55, it must be replicate-controlled and recorded separately from the logloss path.

## 10. Candidate Slice Band

Candidate slice band:

```text
top_8_candidate_packets_fixed_before_projection
```

P55 rows must record the full candidate-pool hash and selected block identity. Selected-only traces are not selector-comparable.

## 11. Block Size

Block size:

```text
1 <= block_size <= 2
```

The first pilot should use singleton and pair blocks only. Larger blocks belong to a later reviewed design.

## 12. Utility Metric

Utility metric:

```text
decomposable_answer_correctness_v1
```

The utility delta is the change in correctness or field-match score for the constrained target when the selected evidence block is added. The metric is decomposable over the declared answer field and can be compared against fixed-model target logloss in a future bridge fit.

Utility evidence is not V-information evidence by itself.

## 13. Logloss Measurement Path

Logloss measurement:

```text
fixed_model_target_logloss_for_declared_answer
```

P55 must record:

- target evidence string or option id;
- target tokenization or answer-option scoring method;
- fixed model tier;
- context `L` hash;
- block `A` ids;
- candidate-pool hash;
- materialization policy;
- decoding/scoring policy;
- measured `delta_logloss` from token logprobs or equivalent forced-choice likelihood.

No `delta_logloss` may be fabricated from utility, rubric score, or model preference.

## 14. Data Source Kind

Primary P55 data source kind:

```text
operator_imported_rows_pending_approval
```

The dry-run config is schema/design only. P55 must not import rows until operator approval is explicit. Fixture rehearsal rows, if later added, would remain engineering-only and paper-ineligible.

## 15. Contamination Policy

Contamination policy:

```text
operator_declared_or_unknown_fail_closed
```

If contamination status is missing, unknown, or failed, P55 must remain paper-ineligible and must not claim measurement validation. Contamination pass alone is not enough for measurement validation.

## 16. Claim Gate

P55 must apply the P53 diagnostic threshold contract and a bridge claim gate before any bridge-facing label is allowed.

Required fail-closed mapping:

| Condition | Required result |
|---|---|
| P54 design only | `metric_claim_level_max = none` |
| no P54 independent acceptance | P55 blocked |
| no operator approval for imported/live/human rows | P55 blocked |
| missing, stale, mismatched, underpowered, or failed `MetricBridgeWitness` | `ambiguous_metric` or `operational_utility_only` |
| fixture-only rows | paper-ineligible; no `vinfo_proxy_supported`; no `calibrated_proxy_supported` |
| synthetic-only rows | structural-only; no `vinfo_proxy_supported`; no `calibrated_proxy_supported` |
| residual/stability/ESS gates fail | `ambiguous_metric` or `operational_utility_only` |
| current P45 `bio_attribute` stratum | remains non-calibrated; no claim inheritance |
| missing human labels or kappa | no measurement validation |

## 17. Negative Controls

Required negative controls for P55:

- redundancy-heavy cases;
- pairwise-complementarity cases;
- underpowered/noisy cases expected to produce `ambiguous_metric`;
- stale or mismatched bridge witness cases expected to fail closed;
- candidate-pool hash mismatch cases expected to be paper-ineligible;
- distractor evidence packets;
- prerequisite-missing cases;
- qualifier-sensitive cases;
- source-conflict cases.

These controls are design requirements only. P54 does not create the rows.

## 18. P55 Operator Gates

P55 is blocked unless:

1. P54 independent review accepts the design;
2. the operator approves the selected data source;
3. imported/live/human rows, if used, have explicit provenance and contamination status;
4. live API execution, if ever requested, receives separate operator approval;
5. human labels or human-human kappa, if ever requested, receive separate operator approval and protocol review.

No live API, credential, human-label, kappa, or external-service action is part of P54.

## 19. Dry-Run Config Description

Dry-run config:

```text
configs/runs/bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json
```

The config records the selected stratum, P53 contract reference, candidate-slice/block policies, operator gates, negative controls, expected P55 outputs, and claim boundaries. It contains no timestamps, UUIDs, absolute local paths, secrets, API keys, machine-specific fields, live API enablement, input rows, or output artifacts.

## 20. Expected P55 Outputs

If P55 is later approved and executed, expected outputs should include:

- imported row manifest with full dispatch identity;
- canonical bridge-calibration pairs;
- bridge fit report with `c_s` fit on development split;
- held-out `zeta_s` residual bound;
- sign agreement and rank correlation;
- ESS and drift-status report;
- active-stratum match report;
- claim-gate report;
- human-readable bridge report.

These outputs are expected P55 outputs only. P54 does not create them.

## 21. Stop Conditions

Stop before P55 if any of these occur:

- P54 independent review does not accept the design;
- operator approval for imported/live/human rows is absent;
- target evidence is not explicit;
- logloss measurement path is unavailable;
- candidate-pool hash or selected block identity is missing;
- materialization policy is not fixed;
- contamination status is failed for a claim-bearing run;
- P55 would require live APIs or human labels without a separate operator gate;
- any result would be described as measurement validation, deployed V-information verification, paper-grade fixture evidence, or P45 `bio_attribute` bridge success.

## 22. Claim Boundaries

P54 does not claim:

- measurement validation;
- human-label validation;
- human-human kappa;
- deployed V-information verification;
- theorem-level deployed submodularity verification;
- synthetic evidence as bridge evidence;
- fixture evidence as paper-grade evidence;
- replay usability as metric support;
- extraction audit as selector validity;
- `ReprojectionWitness` as deployed runtime improvement;
- current P45 `bio_attribute` stratum as `calibrated_proxy_supported`;
- P54 design as `calibrated_proxy_supported`;
- P54 design as `vinfo_proxy_supported`.

P54 is a design review only. Any future P55 bridge claim must be restricted to the exact reviewed active stratum and must pass the P53 threshold contract, active-stratum match, data-source, contamination, ESS, residual, and stability gates.
