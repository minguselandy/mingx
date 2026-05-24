# PAPER-REV-8 / independent final claim audit

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
Perform an independent claim-boundary audit across manuscript-facing docs after PAPER-REV-1 through PAPER-REV-7. This goal should not introduce new manuscript content except corrections required to remove claim violations.

Review targets:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/paper/final-reviewer-response-bank.md`

Run forbidden-claim grep over active docs/tests/scripts, excluding `.git`, `.codex`, raw artifacts, old goal packs, and excluded leftovers:
```bash
grep -RIn --exclude-dir=.git --exclude-dir=.codex --exclude-dir='mingx_*_codex_goals' \
  -E "teacher-forced NLL support|fixed-target continuation scoring support|metric bridge support|calibrated_proxy_supported|vinfo_proxy_supported|measurement validation|human/external gold validation|paper-grade evidence|selector superiority|global selector superiority|Route 5 unlock|Route 8 unlock" \
  docs tests scripts cps || true
```

Audit checklist:
- no measurement validation claim
- no human/external gold validation claim
- no fixed-target NLL claim
- no teacher-forced scoring claim
- no metric bridge claim
- no calibrated_proxy_supported claim
- no vinfo_proxy_supported claim
- no paper-grade evidence claim
- no selector superiority claim
- no global selector superiority claim
- no Route 5 / Route 8 unlock
- raw API responses not stored
- judge labels described as weak evidence only
- operational replay described as scoped only
- extraction audit described as extraction-risk diagnostic only
- reprojection described as operational witness only

Create:
- `docs/reviews/PAPER-REV-8-independent-final-claim-audit.md`

Verdict options:
- ACCEPT
- ACCEPT_WITH_NOTES
- REQUEST_CHANGES
- BLOCK

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
python -m compileall cps tests scripts
```

Done condition:
- Independent final claim audit doc written.
- Verdict assigned.
- Any corrections are docs-only and claim-safe.
- No claim upgrade introduced.
