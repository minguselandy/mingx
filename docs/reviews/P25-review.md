# P25 Empirical Validation Protocol Review

```yaml
phase_id: P25
phase_title: Empirical Validation Protocol
document_type: protocol_review
branch: codex/p24-manuscript-narrative-claim-boundary-revision
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
live_cohort_run: false
runtime_code_changed: false
source_manuscript_changed: false
original_repo_synced: false
coexists_with: docs/reviews/P25-supervisor-review-package.md
```

## 1. Phase Summary

P25 adds a protocol-only empirical validation package for future controlled live
API and human-labeled measurement validation. It does not run live APIs, implement
a live runner, add model clients, add SDKs, modify `reference/`, unblock P04/P09,
or claim `measurement_validated`.

This P25 empirical protocol intentionally coexists with the earlier supervisor
review package at:

```text
docs/reviews/P25-supervisor-review-package.md
```

The supervisor package is not modified by this phase.

## 2. Changed Files

- `docs/protocols/empirical-validation-protocol.md`
- `docs/protocols/human-label-kappa-protocol.md`
- `docs/protocols/contamination-audit-protocol.md`
- `docs/reviews/P25-review.md`

## 3. Validation Protocol Coverage

| Protocol area | Coverage added |
| --- | --- |
| Validation ladder | EV0 replay/determinism, EV1 proxy-regime diagnostics, EV2 controlled live API pilot, EV3 human-labeled measurement validation, EV4 metric-bridge closure. |
| Experimental conditions | No-CPS baseline, heuristic/simple selector baseline, CPS runtime-audit scaffold, optional full/large-context upper baseline. |
| Pilot design | 30-50 case pilot, 100-200 case expansion, fixed endpoint, frozen prompts, temperature policy, run manifest, artifact capture. |
| Required artifacts | Per-case input, candidate pool, projection artifacts, metric bridge witness, projection bundle, output, claim gate, labels, adjudication, kappa, and contamination artifacts. |
| Human labels | Required dimensions, 0/1/2 scale, at least two annotators, adjudication policy. |
| Kappa | Conservative thresholds and low-kappa response. |
| Contamination | Leakage, prompt/dev exposure, candidate-pool answer leakage, baseline fairness, annotator leakage, duplicates, post-hoc tuning. |
| Metric bridge freshness | Missing, stale, current, and fresh-enough-for-review bridge states. |
| Manuscript impact | Separates pre-validation wording, EV2 pilot wording, and EV3/EV4 validation wording. |

## 4. Claims Allowed

| Claim level | Allowed only when |
| --- | --- |
| `engineering_smoke_only` | Local/offline smoke evidence exists. |
| `replayable_artifact_evidence` | Deterministic replay artifacts are complete and stable. |
| `synthetic_structural_only` | Synthetic/proxy regime diagnostics support structural evidence. |
| `operational_utility_only` | Operational metric evidence exists without full bridge closure. |
| `pilot_only` | A controlled pilot exists but validation evidence is incomplete, or contamination fails. |
| `measurement_validated_candidate` | EV3 evidence is strong enough for review, but final bridge/claim gate closure is not complete. |
| `measurement_validated` | Complete artifacts, controlled live run, human labels, acceptable kappa, contamination pass, fresh metric bridge, and claim gate allow all hold. |

## 5. Claims Denied

- `measurement_validated` is denied for the current P17-P25 evidence state.
- Scientific validation is denied for offline engineering, replay, and manuscript
  summary evidence.
- Deployed V-information certification is denied for proxy-regime diagnostics.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.
- Kappa alone is not measurement validation.
- Replay package completeness is not scientific validation.
- Synthetic benchmark success is not deployed V-information certification.
- Paper-facing summaries do not upgrade claim levels.

## 6. P04/P09 Status

| Phase | Status | P25 effect |
| --- | --- | --- |
| P04 | deferred/operator-required | Not unblocked. Human labels, kappa, contamination closure, and bridge review remain future operator-required work. |
| P09 | `BLOCKED_OPERATOR_REQUIRED` | Not unblocked. External runtime integration remains future operator-required work. |

## 7. Next Recommended Phase

Next recommended phase:

```text
P26 Controlled Live API Pilot Runner Design
```

P26 should remain a design phase unless explicitly approved for live execution.
It should specify runner interfaces, manifests, artifact directories, safety
checks, and operator approvals without running live APIs by default.

## 8. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 9. Claim Boundary

- P25 is protocol/documentation only.
- P25 does not edit `docs/archive/context_projection_revised_v10.md`.
- P25 does not add code or tests.
- P25 does not run live APIs or a live cohort.
- P25 does not add a live runner, model API client, external SDK, adapter, exporter, or claim-gate system.
- P25 does not modify `reference/`.
- P25 does not touch stash.
- P25 does not sync to the original repo.
- P25 does not push a PR.
- P25 does not unblock P04 or P09.
- P25 does not claim `measurement_validated`.
