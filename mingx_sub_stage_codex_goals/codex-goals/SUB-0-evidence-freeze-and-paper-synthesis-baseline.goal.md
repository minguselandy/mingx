# Goal ID: SUB-0 / POST-LAPI evidence freeze and paper-synthesis baseline

## Objective

Freeze the completed POST-LAPI candidate operational evidence package and prepare it for manuscript integration and reviewer review. Do not run new experiments.

## Current baseline

- Branch: `codex/integrated-validation-workbench`
- Latest pushed commit: `ce1f7fa307bcacf794befc49eb34beb8f4e4c1e8`
- Recent commit: `POST-LAPI add pilot audit outputs`
- EPF / PAPER-RS / LAPI completed and merged
- POST-0 through POST-8-CONFIG completed
- POST-3 through POST-7 pilots completed
- Current claim: `operational_utility_only/no_claim_upgrade`
- Route 5 locked
- Route 8 locked
- Raw API responses not stored

## Hard constraints

- Do not run live API calls.
- Do not start new experiments.
- Do not scale silver labels.
- Do not unlock Route 5 or Route 8.
- Do not compute or claim teacher-forced NLL.
- Do not claim fixed-target continuation scoring.
- Do not claim metric bridge support.
- Do not claim `calibrated_proxy_supported`.
- Do not claim `vinfo_proxy_supported`.
- Do not claim measurement validation.
- Do not claim human/external gold validation.
- Do not claim paper-grade evidence.
- Do not claim selector superiority or global selector superiority.
- Do not store raw API responses.
- Do not use `git add -A`.
- Do not stage unrelated untracked leftovers.

## Inputs to summarize

- POST-3 judge stability artifacts
- POST-4 sufficiency / abstention artifacts
- POST-5 reprojection witness artifacts
- POST-6 operational replay expansion artifacts
- POST-7 extraction quality audit artifacts
- JSON / JSONL validation outputs
- secret scan / raw-response-storage scan / forbidden-path scan outputs
- existing claim gate contracts
- existing manuscript integration docs

## Create or update

- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/reviews/POST-LAPI-evidence-freeze-review.md`
- `artifacts/audits/post_lapi_evidence_freeze/manifest.json`
- `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256`
- `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json`

## Evidence-freeze ledger requirements

Include:

- commit hash
- branch
- pushed remote status
- live API call counts by POST goal
- normalized row counts by POST goal
- artifact counts
- JSON / JSONL validation counts
- scan results
- compileall result
- focused test result
- claim level
- allowed claims
- denied claims
- Route 5 / Route 8 lock status
- raw_response_stored=false confirmation

## Main results table requirements

Create paper-ready tables for:

1. Backend capability and claim boundary
2. POST-3 judge stability
3. POST-4 sufficiency / abstention
4. POST-5 reprojection witness
5. POST-6 matched-budget operational replay
6. POST-7 extraction quality audit
7. JSON/JSONL and artifact hygiene
8. Denied claims / no-claim-upgrade table

For every result table include:

- evidence source
- sample size / row count / call count
- primary metric
- allowed claim
- denied claim
- paper section target
- whether human labels are present
- whether metric bridge is present
- whether Route 5 or Route 8 is unlocked

## Specific known metrics to include

POST-3:

- live API calls: 240
- 30 examples / 240 normalized rows
- duplicate agreement: 0.9833
- order-swap agreement: 0.9833
- rubric paraphrase agreement: 0.9667
- gate: `weak_evidence_candidate_ready`

POST-4:

- final artifact run: 50 calls
- total turn calls: 100
- gate: `sufficiency_abstention_candidate_ready`
- diagnostic label: `sufficiency_abstention_diagnostic_only`

POST-5:

- live API calls: 26
- gate: `reprojection_witness_candidate_ready`
- repair candidate rate: 0.576923
- label change rate: 0.576923
- unsupported-to-supported rate: 0.576923
- parse failed rate: 0.0

POST-6:

- live API calls: 0
- 2,000 normalized replay records
- 200 HotpotQA candidate pools
- budgets: `512`, `1024`
- oracle marked `non_deployable_upper_bound`

POST-7:

- live API calls: 100
- 100 normalized extraction audit records
- 10 records per stratum
- final gate: `post7_extraction_quality_audit_completed`
- value-weighted loss proxy: 0.197403

Validation:

- focused POST-3 to POST-7 tests + guardrails: `59 passed`
- JSON validation: 27 JSON files
- JSONL validation: 5 JSONL files / 2,416 JSONL rows
- secret scan / raw-response-storage scan / forbidden-path scan: passed
- compileall: passed

## Commands / checks

Run:

```bash
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git rev-parse origin/codex/integrated-validation-workbench
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
python -m compileall cps tests scripts
```

Run a forbidden-claim grep over active docs/tests/scripts, excluding `.git`, `.codex`, raw artifacts, and unrelated leftovers, for:

- teacher-forced NLL support
- fixed-target continuation scoring support
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- measurement validation
- human/external gold validation
- paper-grade evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

## Done condition

- Evidence freeze ledger created.
- Main paper results tables created.
- Claim-boundary summary created.
- Review doc created.
- Manifest and checksums created.
- Checks pass or failures are documented.
- No live API calls were run.
- No new experiments were started.
- No unrelated leftovers were staged.
- No claim upgrade was introduced.

## Report

- changed files
- artifact freeze manifest path
- checks run and results
- claim level
- live API calls run during this goal
- raw_response_stored status
- Route 5 / Route 8 status
- whether commit is recommended
