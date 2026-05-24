# PAPER-REV-9 / final paper readiness summary

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
Create the final paper-readiness summary after manuscript modification goals complete. This is the handoff document for final PR review or submission packaging.

Prerequisite:
- PAPER-REV-8 verdict is `ACCEPT` or `ACCEPT_WITH_NOTES`.

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

Create:
- `docs/reviews/PAPER-REV-9-final-paper-readiness-summary.md`
- `docs/paper/final-paper-modification-summary.md`

The readiness summary must include:
- branch
- commit hash
- remote alignment status
- tracked worktree status
- staged status
- excluded untracked leftovers category summary
- completed paper-revision goals
- changed manuscript-facing files
- changed review/package files
- main evidence table inventory
- claim ceiling
- denied claims
- Route 5 / Route 8 lock status
- raw_response_stored=false status
- checks run and results
- final recommendation: `ready_for_final_review` or `request_changes`

Do not commit automatically.
If the final recommendation is `ready_for_final_review`, include a suggested selective commit plan and commit message:
```text
PAPER-REV finalize claim-safe submission manuscript package
```

Done condition:
- Final paper readiness summary written.
- Final paper modification summary written.
- No new experiments run.
- No claim upgrade introduced.
