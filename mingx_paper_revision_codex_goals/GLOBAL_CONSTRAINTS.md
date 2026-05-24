# GLOBAL_CONSTRAINTS — Mingx Paper Revision Stage

Current phase: **submission-ready / final manuscript revision / final review**.

Current baseline reported by owner:
- Branch: `codex/integrated-validation-workbench`
- Baseline HEAD: `ead306ba97fe9a85a881f1b0e931badf1edf2278`
- Remote branch: aligned, ahead/behind `0/0`
- Tracked worktree: clean
- Staged files: empty
- Remaining files: excluded untracked leftovers only
- SUB-4 decision: `NO_MORE_EXPERIMENTS_RECOMMENDED`
- Handoff verdict: `ACCEPT_WITH_NOTES`

Current claim ceiling:
- `operational_utility_only/no_claim_upgrade`

Locked routes and unsupported capabilities:
- Route 5: locked
- Route 8: locked
- true fixed-target teacher-forced NLL: unsupported
- fixed-target continuation scoring: unsupported
- metric bridge support: unsupported
- human/external measurement validation: absent
- raw API responses: not stored

Allowed evidence classes:
- operational replay evidence
- candidate operational evidence
- model-adjudicated weak evidence
- sufficiency / abstention diagnostic
- operational reprojection witness
- extraction-risk diagnostic
- replayable artifact evidence
- fail-closed bridge audit
- scoped operational improvement under matched budgets

Denied claims:
- measurement validation
- human/external gold validation
- fixed-target teacher-forced NLL support
- fixed-target continuation scoring support
- teacher-forced scoring support
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- paper-grade evidence / paper evidence
- deployed V-information verification
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

Repository hygiene rules:
- Do not run live API calls.
- Do not run new experiments.
- Do not rerun POST-3 through POST-7.
- Do not scale silver labels.
- Do not store raw API responses.
- Do not use `git add -A`.
- Do not stage excluded untracked leftovers.
- Do not delete historical leftovers.
- Do not modify raw evidence artifacts unless a goal explicitly asks for a checksum/index doc that references them.

Excluded leftovers categories to keep isolated:
- Beta leftovers
- Route4D leftovers
- Route6C leftovers
- WS0 / WS1 leftovers
- teacher-forced backend leftovers
- EPF WS6 nested ledger leftovers
- old goal packs
- unrelated excluded leftovers
- `.codex/goal-state/`
- `.codex/automation-state/`
- `artifacts/operator_inputs/`
- raw API dumps
- raw dataset mirrors
