# Goal ID: POST-1 / Artifact replay integrity configuration and offline audit

## Objective

Configure and run an offline artifact replay-integrity audit over existing EPF-FINAL, PAPER-RS, and LAPI artifacts. This goal must not run live API calls.

## Read first

- `configs/post-lapi/artifact_replay_integrity_config.yaml` if installed
- `docs/api/live-api-capability-contract.md`
- `docs/paper/live-api-experiment-boundaries.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/experiments/EPF-final-live-api-silver-label-candidate-package.md`
- Existing LAPI artifact schema and claim guardrail docs

## Hard constraints

- No live API calls.
- No new model judging.
- No new silver labels.
- No Route 5 or Route 8 unlock.
- No raw API response storage.
- No claim upgrade.
- Do not stage unrelated leftovers.
- Do not scan or import `artifacts/operator_inputs`, raw API dumps, or `.codex` state as evidence.

## Implement or update

- `configs/post_lapi/artifact_replay_integrity_config.yaml`
- `scripts/audit_projection_bundle_integrity.py`
- `artifacts/audits/post_lapi_replay_integrity/summary.json`
- `artifacts/audits/post_lapi_replay_integrity/summary.csv`
- `docs/experiments/POST-LAPI-artifact-replay-integrity-audit.md`

## Audit metrics

Compute:
- bundle_count
- schema_valid_count
- schema_valid_rate
- ProjectionPlan presence
- BudgetWitness presence
- MaterializedContext presence
- MetricBridgeWitness presence
- ClaimLedger presence
- selected_evidence_ids presence
- excluded_evidence_ids presence
- materialization_order presence
- downstream_prompt_hash presence
- model_snapshot / endpoint presence
- raw_response_stored=false rate
- replay reconstruction pass/fail
- claim boundary consistency
- denied-claim leakage count

## Claim rules

Allowed:
- replayable_artifact_evidence
- artifact_hygiene_evidence
- operational_audit_evidence

Denied:
- scientific validation
- measurement validation
- paper-grade evidence
- metric bridge support
- vinfo_proxy_supported
- selector superiority

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
python -m compileall cps tests scripts
```

## Done condition

- Audit config exists.
- Audit script runs on existing artifacts without live API calls.
- Summary JSON and CSV are produced.
- Paper-facing audit doc is written.
- No claim upgrade is introduced.
- Do not commit automatically unless explicitly instructed after review.


Report format:
- Goal ID:
- Branch:
- HEAD:
- Changed files:
- Staged files:
- Checks run:
- Check results:
- Live API calls run: yes/no
- Raw API responses stored: yes/no
- Claim level:
- Claim upgrade introduced: yes/no
- Route 5 locked: yes/no
- Route 8 locked: yes/no
- Unrelated leftovers staged: yes/no
- Next recommended goal:
