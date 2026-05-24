# PAPER-REV-5 / limitations, conclusion, nonclaims

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
Polish Limitations, Conclusion, and nonclaim documents so the paper ends with a strong but conservative operational-audit claim.

Primary files to review and update if present:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/submission-limitations.md`
- `docs/paper/final-submission-nonclaims.md`
- `docs/paper/final-conclusion-claim-safe.md`
- `docs/paper/submission-claim-ledger.md`

Required limitations:
- No fixed-target teacher-forced NLL.
- No fixed-target continuation scoring.
- Generated-token logprobs are output-side diagnostics only.
- No metric bridge support.
- No calibrated proxy support.
- No V-information proxy support.
- No human/external gold validation.
- No measurement validation.
- No selector superiority.
- Operational replay is scoped by dataset, budgets, baselines, and materialization/evaluator regime.
- Extraction audit is model-adjudicated extraction-risk evidence only.
- Judge outputs are weak evidence only.

Required conclusion posture:
```text
The present evidence is operational rather than validating. The contribution is a replayable, claim-gated operational audit framework for dispatch-time evidence projection under live-API constraints.
```

Create:
- `docs/reviews/PAPER-REV-5-limitations-conclusion-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Limitations and conclusion preserve no_claim_upgrade.
- Nonclaims are explicit and easy for reviewers to find.
- No claim upgrade introduced.
