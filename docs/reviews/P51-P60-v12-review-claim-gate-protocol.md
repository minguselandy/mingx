# Mingx v12 Follow-up Review and Claim-Gate Protocol: P51-P60

Status: proposed review protocol
Project: `mingx`
Applies to: P51-P60 follow-up development and experiment cycle
Primary anchors: `docs/archive/context_projection_fixed_v12.md`, `docs/paper-alignment-v12.md`, `docs/reviews/P45-P50-v12-phase-summary.md`
Date: 2026-05-11

---

## 0. Review purpose

This document defines how to review the next mingx development and experiment cycle without weakening the v12 paper boundary. The review protocol is intentionally conservative. It treats missing evidence, stale bridges, fixture-only data, synthetic-only data, and underpowered samples as reasons to downgrade or abstain, not as reasons to relabel a result as successful.

The reviewer's task is not to make the project look more complete. The task is to decide what the current artifact actually supports.

---

## 1. Required reading before review

Every reviewer must read these files before issuing a verdict:

1. `AGENTS.md`
2. `docs/paper-alignment-v12.md`
3. `docs/archive/context_projection_fixed_v12.md`
4. `docs/reviews/P45-P50-v12-phase-summary.md`
5. `docs/experiments/P45-bridge-calibration-closure.md`
6. the phase plan under review
7. the changed files and generated artifacts

For P56/P59 replay work, also read:

- `docs/protocols/phase-b-replay-protocol.md`

For P57 extraction work, also read:

- `docs/experiments/extraction-audit-pilot-v12.md`

For P55 bridge work, also read:

- `docs/experiments/P45-bridge-calibration-closure.md`
- the P54 new-stratum design review

---

## 2. Review verdicts

Allowed verdicts:

| Verdict | Meaning | May auto-advance? |
|---|---|---:|
| `ACCEPT` | phase meets scope, tests, and claim boundary | yes, if no operator/scientific gate |
| `ACCEPT_WITH_NOTES` | phase meets core requirements but has non-blocking notes | yes, if notes do not involve operator/scientific gate |
| `REQUEST_CHANGES` | phase has fixable issues | no |
| `BLOCKED_OPERATOR_REQUIRED` | next step requires live API, credentials, human labels, kappa, external service, or scientific claim review | no |
| `REJECT` | phase violates scope or claim boundary | no |

Auto-advance is never allowed when the next phase requires:

- live API execution;
- credentials or secrets;
- human annotation;
- human-human kappa;
- external services;
- license review;
- a new scientific claim tier;
- promotion of fixture/synthetic/replay-only evidence to paper-grade evidence.

---

## 3. Required review metadata block

Every review file must begin with this metadata block.

```yaml
phase: P<NN>
phase_name: <name>
reviewer: <name-or-window-id>
date: <YYYY-MM-DD>
verdict: ACCEPT | ACCEPT_WITH_NOTES | REQUEST_CHANGES | BLOCKED_OPERATOR_REQUIRED | REJECT
blocked: true | false
requires_operator: true | false
next_phase_allowed: true | false
metric_claim_level_max: vinfo_proxy_supported | calibrated_proxy_supported | operational_utility_only | ambiguous_metric | none
selector_regime_label_max: greedy_supported | pairwise_escalate | higher_order_risk | ambiguous | none
paper_evidence_eligible: true | false
measurement_validation_claim: false
live_api_used: true | false
human_labels_present: true | false
human_human_kappa_present: true | false
contamination_status: pass | fail | unknown | not_applicable
```

Rules:

- `measurement_validation_claim` must remain `false` unless a separate human-label, kappa, contamination, and metric-bridge review explicitly authorizes a candidate claim.
- `paper_evidence_eligible` must remain `false` for fixture-only, synthetic-only, underpowered, stale-bridge, and replay-completeness-only runs.
- `next_phase_allowed` must be `false` if `requires_operator` is `true`.

---

## 4. Hard rejection conditions

Issue `REJECT` or `REQUEST_CHANGES` if any of these appear as active claims:

- `Vinfo_proxy_certified`
- `greedy_valid`
- `measurement_validated`
- deployed V-information verification
- theorem-level deployed submodularity verification
- synthetic evidence as bridge evidence
- fixture evidence as paper-grade evidence
- replay usability as metric support
- extraction audit as selector validity
- `ReprojectionWitness` as deployed runtime improvement
- current P45 `bio_attribute` stratum as `calibrated_proxy_supported`
- utility score as V-information proxy evidence without valid matching `MetricBridgeWitness`

Issue `REQUEST_CHANGES` if any paper-facing doc maps:

```text
synthetic-only evidence -> vinfo_proxy_supported
fixture-only evidence -> calibrated_proxy_supported
fixture-only evidence -> vinfo_proxy_supported
model-adjudicated fixture -> human label or kappa
```

Issue `REQUEST_CHANGES` if the GitHub manuscript still contains a damaged proof string such as:

```text
sum_{j 0
```

Issue `REQUEST_CHANGES` if root `README.md` or `docs/README.md` still describes closed P45 work as the next active priority after P51 begins.

---

## 5. Claim-boundary matrix

### 5.1 Metric claim review

| Evidence state | Maximum allowed `metric_claim_level` |
|---|---|
| valid log-loss alignment plus reviewed formal/fixed-model bridge | `vinfo_proxy_supported` |
| valid fresh utility-to-logloss bridge for active stratum | `calibrated_proxy_supported` |
| utility diagnostics without bridge | `operational_utility_only` |
| bridge missing, stale, underpowered, mismatched, or failed | `ambiguous_metric` or `operational_utility_only` |
| synthetic-only structural oracle | `ambiguous_metric` |
| fixture-only realistic task | `operational_utility_only` at most |
| current P45 `bio_attribute` closure | `ambiguous_metric` for P45e artifact; downstream utility `operational_utility_only` |

### 5.2 Selector label review

| Evidence state | Allowed selector label |
|---|---|
| bridge fresh, signal adequate, pair ratio healthy, pairwise excess low, SAG gap small | `greedy_supported` |
| pairwise complementarity or meaningful SAG improvement | `pairwise_escalate` |
| triple/prerequisite sentinel fires or hidden synergy conflict appears | `higher_order_risk` |
| low signal, underpowered sample, failed audit, stale bridge, or conflicting signals | `ambiguous` |

### 5.3 Paper evidence eligibility

| Artifact/data kind | Paper evidence eligible? | Notes |
|---|---:|---|
| deterministic synthetic structural benchmark | false by default | may appear as structural smoke test, not validation |
| deterministic fixture realistic-task benchmark | false | workflow/schema evidence only |
| replay package completeness | false | replayability is not metric support |
| imported realistic replay with fresh valid bridge | possible | must pass phase-specific review |
| bridge pilot with fresh valid active stratum | possible for bridge claim | not measurement validation |
| human sentinel extraction audit | possible as sentinel evidence | not full validation unless separately reviewed |
| live API smoke | false by itself | operational feasibility only |

---

## 6. Phase-specific review checklists

## P51 review — state reconciliation and guardrail cleanup

Reviewer must check:

- [ ] root `README.md` no longer says P45 is the next priority.
- [ ] `docs/README.md` no longer says P45 is the next priority.
- [ ] P45-P50 are described as completed scaffold/reference phases.
- [ ] `docs/templates/claim-boundary-checklist.md` no longer maps synthetic-only evidence to `vinfo_proxy_supported`.
- [ ] legacy labels appear only as denied/compatibility/archive language.
- [ ] no evidence claim was upgraded.
- [ ] guardrail tests were added or existing tests were shown to cover the issue.

Required verdict logic:

- `ACCEPT` if all state-entrypoint issues are fixed and guardrails pass.
- `ACCEPT_WITH_NOTES` if docs are fixed but a new guardrail test is deferred with a clear reason.
- `REQUEST_CHANGES` if any paper-facing doc still contains the synthetic-to-vinfo mapping.

## P52 review — manuscript proof and evidence-state integration

Reviewer must check:

- [ ] Appendix B proof no longer contains damaged summation text.
- [ ] the telescoping, pairwise-additive, degree cap, and final summation steps are complete.
- [ ] Section 3.4 / 4.7 acknowledges P45 closure.
- [ ] the paper states that the current `bio_attribute` stratum is non-calibrated.
- [ ] the paper does not claim `calibrated_proxy_supported` for current P45.
- [ ] future-work wording is updated to “new stratum or materially new design.”
- [ ] `vinfo_proxy_supported` definition is stricter, not looser.
- [ ] no certification framing is introduced.

Required verdict logic:

- `ACCEPT` if proof and evidence-state issues are resolved.
- `REQUEST_CHANGES` if the proof remains broken or the P45 negative closure is omitted.

## P53 review — diagnostic threshold contract

Reviewer must check:

- [ ] threshold contract records active stratum and calibration epoch.
- [ ] LCB method or conservative fallback is predeclared.
- [ ] signal threshold, ratio threshold, pairwise excess threshold, SAG gap threshold, triple sentinel threshold, and ESS gate are specified or explicitly inactive with fail-closed behavior.
- [ ] underpowered, stale, fixture-only, and synthetic-only cases cannot emit upgraded claims.
- [ ] `MetricBridgeWitness` semantics are preserved.
- [ ] the contract is described as protocol/audit scaffold, not validation.

Required verdict logic:

- `ACCEPT` if the contract is deterministic and fail-closed.
- `REQUEST_CHANGES` if thresholds can be inferred post hoc without record.

## P54 review — new bridge stratum design

Reviewer must check:

- [ ] design is materially distinct from the closed P45 `bio_attribute` stratum.
- [ ] task family, target type, model tier, materialization policy, decoding policy, candidate slice, and block size are fixed.
- [ ] logloss target evidence is explicit.
- [ ] utility metric is decomposable or bridge rationale is stated.
- [ ] negative controls are specified.
- [ ] contamination and data-source policies are stated.
- [ ] live API/human/operator gates are explicit.
- [ ] P55 is blocked unless design review accepts.

Required verdict logic:

- `ACCEPT` if one new stratum is justified and executable as dry-run/imported protocol.
- `BLOCKED_OPERATOR_REQUIRED` if execution requires live APIs or operator-imported rows.
- `REQUEST_CHANGES` if the design merely retries P45 without new rationale.

## P55 review — new-stratum bridge pilot

Reviewer must check:

- [ ] P54 design was accepted.
- [ ] data source was operator-approved if imported/live/human data were used.
- [ ] rows include full dispatch identity and candidate-pool hashes.
- [ ] target evidence and logloss measurement path are present.
- [ ] `c_s` is fit on development data only.
- [ ] `zeta_s` is reported on held-out data.
- [ ] sign agreement, rank correlation, residual stability, and ESS are reported.
- [ ] active-stratum match is exact before any claim inheritance.
- [ ] failed residual/ESS/stability gates produce `ambiguous_metric` or `operational_utility_only`.
- [ ] fixture-only data do not become paper evidence.

Required verdict logic:

- `ACCEPT` if bridge decision follows predeclared gates.
- `ACCEPT_WITH_NOTES` if pilot fails but fail-closed report is correct.
- `REQUEST_CHANGES` if claims are upgraded despite failed gates.
- `BLOCKED_OPERATOR_REQUIRED` if additional live/human data are needed.

## P56 review — realistic dispatch replay substrate

Reviewer must check:

- [ ] replay trace includes `run_id`, `dispatch_id`, `agent_id`, and `round_id`.
- [ ] complete considered candidate set is available.
- [ ] candidate-pool hash is stable and bound to artifacts.
- [ ] `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, and `MetricBridgeWitness` are present or missingness is classified.
- [ ] selected-only traces are not treated as selector-comparable.
- [ ] candidate-pool hash mismatch fails closed.
- [ ] replay usability is not treated as metric support.

Required verdict logic:

- `ACCEPT` if classification is deterministic and conservative.
- `REQUEST_CHANGES` if missing identity or candidate-pool mismatch still produces headline eligibility.

## P57 review — extraction audit v2

Reviewer must check:

- [ ] extraction-risk strata are defined.
- [ ] labels distinguish missing, unsupported, over-merged, qualifier-loss, temporal-scope, contradiction, and provenance-loss cases.
- [ ] value-weighted extraction loss is computed separately from bridge notation.
- [ ] model-adjudicated audit is not called human validation.
- [ ] human sentinel, if present, records annotator/agreement details.
- [ ] missing human labels or kappa do not block fixture audit, but do block measurement-validation claims.
- [ ] extraction results do not upgrade selector-regime or metric-bridge claims.

Required verdict logic:

- `ACCEPT` if extraction-risk audit is separate from selector validity.
- `REQUEST_CHANGES` if extraction completeness is used as theorem transfer to `M*`.

## P58 review — provenance-aware redundancy diagnostics

Reviewer must check:

- [ ] duplicate redundancy and independent corroboration are separated.
- [ ] adversarial repetition and source conflict trigger audit/escalation, not simple diversity penalty.
- [ ] prerequisite overlap is preserved or escalated appropriately.
- [ ] provenance features are deterministic.
- [ ] selector changes remain heuristic unless separately calibrated.
- [ ] no metric claim is upgraded from redundancy diagnostics alone.

Required verdict logic:

- `ACCEPT` if categories are deterministic and claim-safe.
- `REQUEST_CHANGES` if the diagnostic weakens ambiguity in adversarial cases without evidence.

## P59 review — re-projection replay integration

Reviewer must check:

- [ ] `ReprojectionWitness` binds to full dispatch identity.
- [ ] trigger/action/context diff fields are complete.
- [ ] before/after materialized-context hashes are present.
- [ ] budget status is recorded.
- [ ] identity mismatch or unexplained candidate-pool mismatch fails closed.
- [ ] before/after improvement is not called deployed runtime improvement.
- [ ] missing bridge prevents metric claim upgrade.

Required verdict logic:

- `ACCEPT` if witness auditability is improved without claim overreach.
- `REQUEST_CHANGES` if re-projection is described as validated runtime improvement.

## P60 review — evidence ledger and manuscript package

Reviewer must check:

- [ ] every artifact family has a claim boundary.
- [ ] P45 negative closure is preserved.
- [ ] synthetic and fixture results are paper-ineligible unless explicitly marked structural/scaffold only.
- [ ] paper evidence table separates main-paper evidence from appendix/repo scaffold.
- [ ] denied claims are explicit.
- [ ] manuscript caveat sentences are included.
- [ ] future work does not imply already-established bridge support.

Required verdict logic:

- `ACCEPT` if the evidence ledger can guide manuscript revision safely.
- `REQUEST_CHANGES` if any artifact is overpromoted.

---

## 7. Required test reporting

Every review must include exact commands and exact results.

Use this format:

```text
Checks run:
- uv run pytest tests/test_revised_framing_guardrails.py
  Result: <exact output or summary>
- uv run pytest tests/test_projection_artifacts.py
  Result: <exact output or summary>

Checks not run:
- uv run pytest
  Reason: <doc-only phase / time / missing dependency / operator gate>
```

Do not write “tests passed” without commands and results.

---

## 8. Artifact review checklist

For any generated artifact, verify:

- [ ] deterministic ordering;
- [ ] stable schema version;
- [ ] no timestamps/UUIDs/absolute local paths in canonical outputs unless intentionally noncanonical;
- [ ] source files and config files recorded;
- [ ] full dispatch identity recorded if replay/comparison relevant;
- [ ] candidate-pool hash recorded if selector/replay relevant;
- [ ] materialization policy recorded if metric/replay relevant;
- [ ] metric bridge status recorded if diagnostic labels appear;
- [ ] data source kind recorded;
- [ ] paper eligibility recorded;
- [ ] denied claims recorded.

---

## 9. Manuscript review checklist

For manuscript edits, verify:

- [ ] `Proxy-Regime Diagnosis` remains the framing.
- [ ] certification language is absent or denied.
- [ ] theorem statements apply only to formal `f_i^V` under assumptions.
- [ ] fixed-model logloss and utility proxies are separated.
- [ ] token-budgeted heuristic pipeline is not given cardinality-greedy theorem inheritance.
- [ ] bridge status is fresh/missing/stale/failed, not implied.
- [ ] P45 negative closure is not hidden.
- [ ] synthetic benchmark is structural-only.
- [ ] model-adjudicated labels are not human labels.
- [ ] extraction `M* -> M` is a separate bridge risk.
- [ ] runtime artifacts are audit interfaces, not validation by themselves.

---

## 10. Common reviewer failure modes

Avoid these mistakes:

1. Treating a completed scaffold as empirical validation.
2. Treating a fixture run as paper-grade evidence.
3. Treating a model-adjudicated label as a human label.
4. Treating replay usability as metric support.
5. Treating extraction audit as selector-regime proof.
6. Treating a successful synthetic structural signature as bridge evidence.
7. Treating a `ReprojectionWitness` improvement row as deployed runtime improvement.
8. Treating the current P45 `bio_attribute` stratum as bridge-calibrated.
9. Using `greedy_supported` without the metric and selector gates needed by the phase.
10. Saying “measurement validated” without human labels, agreement, contamination closure, and fresh bridge evidence.

---

## 11. Review output template

````markdown
# P<NN> <Phase Name> Review

```yaml
phase: P<NN>
phase_name: <name>
reviewer: <window/person>
date: <YYYY-MM-DD>
verdict: <ACCEPT|ACCEPT_WITH_NOTES|REQUEST_CHANGES|BLOCKED_OPERATOR_REQUIRED|REJECT>
blocked: <true|false>
requires_operator: <true|false>
next_phase_allowed: <true|false>
metric_claim_level_max: <value|none>
selector_regime_label_max: <value|none>
paper_evidence_eligible: <true|false>
measurement_validation_claim: false
live_api_used: <true|false>
human_labels_present: <true|false>
human_human_kappa_present: <true|false>
contamination_status: <pass|fail|unknown|not_applicable>
```

## Scope reviewed

- Changed files:
  - `<file>`
- Generated artifacts:
  - `<artifact>`

## Summary

<short factual summary>

## Claim-boundary review

- Metric claim ceiling: `<value>`
- Selector label ceiling: `<value>`
- Paper eligibility: `<true/false>`
- Denied claims preserved:
  - `measurement_validated`
  - deployed V-information verification
  - fixture/synthetic paper evidence

## Checks run

```text
<commands and exact results>
```

## Findings

### Blocking findings

- None / list

### Non-blocking notes

- None / list

## Required changes

- None / list

## Next-phase decision

<allowed / not allowed / operator required>
````

---

## 12. Final P51-P60 summary template

At the end of the cycle, create `docs/reviews/P51-P60-v12-phase-summary.md` with:

| Phase | Verdict | Claim ceiling | Paper eligible? | Operator gate? | Main artifact |
|---|---|---|---:|---:|---|
| P51 | TBD | docs only | false | false | state reconciliation |
| P52 | TBD | manuscript only | false | false | proof/evidence integration |
| P53 | TBD | protocol scaffold | false | false | threshold contract |
| P54 | TBD | design only | false | maybe | new stratum design |
| P55 | TBD | bridge claim only if gates pass | maybe | yes if live/import/human | bridge pilot |
| P56 | TBD | replay usability | maybe | maybe | realistic replay |
| P57 | TBD | extraction-risk evidence | maybe | yes if human | extraction audit v2 |
| P58 | TBD | operational diagnostic | false | false | redundancy diagnostics |
| P59 | TBD | operational audit | false | maybe | re-projection replay |
| P60 | TBD | evidence ledger | false by itself | false | paper package |

The summary must explicitly state which claims remain denied.
