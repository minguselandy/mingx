# PAPER-REV-0 / baseline and manuscript-scope lock

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
Confirm that the repository is still at the clean final-review baseline and create a paper-revision scope lock. This goal is verification-first and docs-only.

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

Inspect but do not modify evidence artifacts:
- POST-3 judge stability outputs
- POST-4 sufficiency / abstention outputs
- POST-5 reprojection witness outputs
- POST-6 operational replay outputs
- POST-7 extraction audit outputs
- SUB-0 evidence freeze outputs
- SUB-5 final readiness summary

Create:
- `docs/reviews/PAPER-REV-0-baseline-and-scope-lock.md`

The scope lock must state:
- final paper revision is paper-only
- no new experiments are recommended
- no live API calls are authorized
- evidence package is frozen
- allowed claims and denied claims
- current commit and remote alignment
- tracked worktree status and staged status
- excluded untracked leftovers are out of scope

Done condition:
- Review doc created.
- Checks pass or failures are documented.
- No evidence artifacts are changed.
- No live API calls run.
- No claim upgrade introduced.
