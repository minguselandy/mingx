# PAPER-REV-7 / reviewer defense and response bank

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
Finalize reviewer-defense material for the live-API operational audit paper.

Primary files to review and update if present:
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/paper/submission-reviewer-package.md`
- `docs/paper/final-submission-nonclaims.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`

Create or update:
- `docs/paper/final-reviewer-response-bank.md`
- `docs/reviews/PAPER-REV-7-reviewer-defense-review.md`

The response bank must cover:
1. Why no fixed-target NLL bridge?
2. Why mention V-information at all?
3. Why use LLM judges?
4. Why is this not a context-compression paper?
5. Why not claim selector superiority?
6. What does the live-API-only constraint contribute scientifically?
7. Why are the POST-LAPI results useful if they are not validation?
8. Why no more experiments are recommended?
9. Why raw API responses are not stored?
10. What would be required for future claim upgrade?

Every answer must preserve:
```text
operational_utility_only/no_claim_upgrade
```

Required direct answer for NLL bridge:
```text
The supported live-API route exposes generated output-token diagnostics, not documented fixed-target continuation scoring. We therefore fail closed rather than relabel sampled chat logprobs as teacher-forced NLL.
```

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Reviewer response bank is complete.
- No response implies validation, metric bridge, V-information proxy, or selector superiority.
- No claim upgrade introduced.
