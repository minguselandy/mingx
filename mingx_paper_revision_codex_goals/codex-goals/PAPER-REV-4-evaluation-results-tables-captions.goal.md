# PAPER-REV-4 / evaluation results, tables, captions

Global constraints: read `mingx_paper_revision_codex_goals/GLOBAL_CONSTRAINTS.md` first and obey it throughout this goal.

Current baseline:
- Branch: `codex/integrated-validation-workbench`
- Baseline HEAD: `ead306ba97fe9a85a881f1b0e931badf1edf2278`
- Remote branch aligned: yes
- Tracked worktree clean: yes, per owner report
- Staged files empty: yes, per owner report
- Current claim: `operational_utility_only/no_claim_upgrade`
- Route 5: locked
- Route 8: locked
- SUB-4: `NO_MORE_EXPERIMENTS_RECOMMENDED`

Hard constraints:
- Do not run live API calls.
- Do not run new experiments.
- Do not rerun POST-3, POST-4, POST-5, POST-6, or POST-7.
- Do not scale silver labels.
- Do not unlock Route 5 or Route 8.
- Do not compute or claim fixed-target teacher-forced NLL.
- Do not claim fixed-target continuation scoring.
- Do not claim metric bridge support.
- Do not claim `calibrated_proxy_supported`.
- Do not claim `vinfo_proxy_supported`.
- Do not claim measurement validation.
- Do not claim human/external gold validation.
- Do not claim paper-grade evidence or paper evidence.
- Do not claim selector superiority or global selector superiority.
- Do not store raw API responses.
- Do not use `git add -A`.
- Do not stage excluded untracked leftovers.
- Do not delete excluded untracked leftovers.

Objective:
Finalize Evaluation as `Operational evaluation and weak-evidence diagnostics`, using the completed POST-LAPI results and strict table-level claim labels.

Primary files to review and update if present:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/paper/final-submission-package-map.md`

Required section title:
```text
Operational evaluation and weak-evidence diagnostics
```

Required main table set:
1. Backend capability and claim boundary.
2. POST-3 judge stability:
   - 240 live API calls
   - 30 examples
   - 240 normalized rows
   - duplicate agreement 0.9833
   - order-swap agreement 0.9833
   - rubric paraphrase agreement 0.9667
   - claim: model-adjudicated weak diagnostics only
3. POST-4 sufficiency / abstention:
   - 50 final normalized rows
   - claim: sufficiency-abstention diagnostics only
4. POST-5 reprojection witness:
   - 26 rows
   - repair candidate rate 0.576923
   - label change rate 0.576923
   - unsupported-to-supported rate 0.576923
   - parse failed rate 0.0
   - claim: candidate operational evidence only
5. POST-6 matched-budget operational replay:
   - 2,000 replay records
   - 200 HotpotQA candidate pools
   - budgets 512 and 1024
   - 0 live API calls
   - oracle marked non_deployable_upper_bound
   - claim: scoped operational replay only
6. POST-7 extraction quality audit:
   - 100 records
   - 10 records per stratum
   - value-weighted loss proxy 0.197403
   - claim: extraction-risk diagnostics only
7. Artifact hygiene and evidence freeze:
   - JSON/JSONL validation
   - checksums
   - scans
   - raw_response_stored=false

Every table caption must include:
- evidence tier
- allowed claim
- denied claim
- whether human labels are present
- whether metric bridge is present
- whether Route 5 / Route 8 are locked

Create:
- `docs/reviews/PAPER-REV-4-evaluation-table-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Evaluation table captions cannot be read as validation or selector superiority.
- Table facts match frozen evidence.
- No live API calls run.
- No claim upgrade introduced.
