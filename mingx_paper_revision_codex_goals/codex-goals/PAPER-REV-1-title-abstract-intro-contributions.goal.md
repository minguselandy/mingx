# PAPER-REV-1 / title, abstract, introduction, contribution bullets

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
Make the title, abstract, introduction, and contribution bullets claim-safe and aligned with the completed POST-LAPI evidence package.

Primary files to review and update if present:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/final-abstract-claim-safe.md`
- `docs/paper/final-conclusion-claim-safe.md`
- `docs/paper/submission-experiment-summary.md`

If a listed file is absent, record that in the review doc and update the closest manuscript-facing equivalent.

Required narrative:
- The paper is about dispatch-time evidence selection / context projection in live-agent LLM systems.
- V-information is a formal anchor and organizing lens.
- Current evidence is operational-only.
- The supported live API does not establish fixed-target teacher-forced NLL or fixed-target continuation scoring.
- Generated-token logprobs, constrained label generation, and model-adjudicated labels are operational diagnostics / weak candidate evidence only.
- Contribution bullets should emphasize audit-first operational diagnostics, fail-closed claim gates, replayable artifacts, sufficiency / abstention, reprojection witnesses, operational replay, and extraction-risk audit.

Forbidden language in headline sections:
- validation
- validated proxy
- V-information proxy support
- calibrated proxy
- metric bridge support
- paper evidence
- selector superiority
- fixed-target NLL support
- human gold validation

Create:
- `docs/reviews/PAPER-REV-1-title-abstract-intro-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Headline manuscript framing is claim-safe.
- Review doc records files changed and nonclaims preserved.
- No live API calls run.
- No claim upgrade introduced.
