# PAPER-REV-6 / appendix, artifact index, reproducibility note

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
Finalize the appendix-facing artifact index and reproducibility note without modifying evidence artifacts.

Primary files to review and update if present:
- `docs/paper/final-submission-artifact-index.md`
- `docs/paper/final-submission-package-map.md`
- `docs/paper/final-excluded-leftovers-ledger.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/paper/submission-experiment-summary.md`

Required appendix map:
- manuscript-facing docs
- claim-boundary docs
- evidence ledgers
- POST-3 artifact summary
- POST-4 artifact summary
- POST-5 artifact summary
- POST-6 artifact summary
- POST-7 artifact summary
- evidence freeze checksums
- table inputs
- JSON/JSONL validation artifacts
- scan summaries
- excluded leftovers ledger by category only

Required reproducibility statement:
- No raw API responses are stored.
- Normalized rows, hashes, compact provenance, prompts/templates where appropriate, and checksums are stored.
- Live API model snapshots/endpoints should be documented in artifacts where applicable.
- Replays are operational and scoped; they do not validate V-information.

Do not:
- change JSON/JSONL evidence outputs
- regenerate checksums unless explicitly verifying mismatch
- stage leftovers

Create:
- `docs/reviews/PAPER-REV-6-appendix-reproducibility-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Appendix and artifact index are complete and claim-safe.
- Excluded leftovers are listed only by category.
- No evidence artifacts changed.
- No claim upgrade introduced.
