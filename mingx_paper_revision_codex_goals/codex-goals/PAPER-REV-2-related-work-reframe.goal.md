# PAPER-REV-2 / related work reframe

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
Rewrite or polish related work so the paper is positioned as an audit-first operational diagnostic framework, not as a better compressor/router/validation benchmark.

Primary files to review and update if present:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/related-work-live-api-operational-reframe.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`

Required related-work structure:
1. Context compression and adaptive retrieval comparators.
   - Mention that compression / pruning / routing are crowded and not the novelty claim.
2. Sufficiency, abstention, and long-context diagnostics.
   - Position sufficiency / abstention as the closest positive experimental lane.
3. V-information and budgeted subset-selection theory.
   - V-information motivates usable information, but current experiments do not estimate deployed V-information.
4. LLM-as-judge and weak supervision.
   - Judges are weak noisy signals, not validation.
5. Runtime audit artifacts and claim gates.
   - Emphasize selected/excluded evidence, materialization order, claim ledger, replay witness, and reprojection witness.

Required explicit sentence or equivalent:
```text
We do not claim to be the first context compressor, adaptive RAG router, sufficiency evaluator, automated judge pipeline, or weak-supervision system. Our contribution is a claim-gated operational audit framework for dispatch-time evidence projection under live-API constraints.
```

Create:
- `docs/reviews/PAPER-REV-2-related-work-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Related work no longer invites a selector-superiority or compressor-superiority reading.
- Related work makes the live-API constraint and weak-evidence posture clear.
- No claim upgrade introduced.
