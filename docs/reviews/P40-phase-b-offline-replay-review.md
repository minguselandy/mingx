# P40 Phase B Offline Replay Review

## Review Verdict

`ACCEPT`

## Scope Reviewed

P40 implements the offline Phase B replay package over recorded artifacts. The
review covered:

- replay status and claim-level separation;
- explicit replay precedence;
- fail-closed cached utility/log-loss recomputation;
- headline eligibility and exclusion accounting;
- contamination-failure claim downgrade;
- deterministic replay output files;
- documentation and claim-boundary consistency.

## Files Changed

- `cps/experiments/phase_b_replay.py`
- `tests/test_phase_b_replay.py`
- `docs/experiments/P40-phase-b-offline-replay-implementation-plan.md`
- `docs/reviews/P40-phase-b-offline-replay-review.md`

## Validation

Commands run:

```bash
python -m compileall cps scripts
uv run pytest tests/test_phase_b_replay.py -q
uv run pytest -q
```

Results:

- `python -m compileall cps scripts`: passed
- `uv run pytest tests/test_phase_b_replay.py -q`: `17 passed`
- `uv run pytest -q`: `425 passed, 4 skipped`

Risky claim scan over changed files was reviewed for:

```text
measurement_validated
scientific validation
deployed V-information certification
Vinfo_proxy_certified
certified greedy-valid
human labels
kappa
pilot_only
model_adjudicated_pilot_only
operational_utility_only
```

All remaining occurrences are denied claims, boundary conditions, claim-gate
rules, tests, or claim ceilings.

## Claim-Boundary Review

- No live API was run.
- No human labels were fabricated.
- No human-human kappa was fabricated.
- No contamination pass was fabricated.
- No fresh metric bridge was fabricated.
- No `measurement_validated` claim was introduced.
- Replay package completeness remains replay/observability evidence only.
- Contamination failure preserves the underlying replay status but downgrades
  claim level to `pilot_only` and excludes the row from headline diagnostics.
- Stale or missing metric bridge remains `operational_utility_only` or
  `ambiguous`.
- Headline summaries use only eligible replay rows and account for excluded
  rows separately.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.

## Output Review

Required outputs are implemented:

- `replay_manifest.json`
- `replay_manifest.jsonl`
- `per_dispatch_diagnostics.jsonl`
- `missing_field_report.json`
- `missing_fields.json`
- `pipeline_proxy_alignment.json`
- `metric_claim_level_summary.json`
- `selector_regime_summary.json`
- `replay_status_counts.json`
- `replay_summary.json`
- `report.md`

Byte-stability is covered by `tests/test_phase_b_replay.py`.

## Remaining Limitations

- P40 does not run live inference or fill missing replay fields.
- P40 recomputes only diagnostics supported by cached utility/log-loss records;
  incomplete or uninformative utility evidence fails closed.
- P40 does not create human labels or kappa evidence.
- P40 does not upgrade Route B or replay evidence into measurement validation.

## Next Recommended Milestone

P41 Route B model-adjudicated evaluation, unless the operator chooses a narrower
documentation-only checkpoint first.
