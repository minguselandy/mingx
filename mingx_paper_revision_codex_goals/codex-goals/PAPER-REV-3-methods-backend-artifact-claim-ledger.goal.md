# PAPER-REV-3 / methods, backend capability, artifact bundle, claim ledger

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
Polish Methods so the backend capability boundary, ProjectionBundleV1 audit interface, claim ledger, weak judge protocol, sufficiency/abstention protocol, and reprojection witness are described as method components.

Primary files to review and update if present:
- `docs/archive/context_projection_fixed_v12.md`
- `docs/api/live-api-capability-contract.md`
- `docs/paper/live-api-experiment-boundaries.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/paper/submission-claim-ledger.md`
- `docs/paper/final-submission-artifact-index.md`

Required Methods content:
- Define the dispatch-time projector and regime.
- Define backend capability table in Methods, not only appendix.
- State generated-token logprobs are output-side confidence diagnostics only.
- State fixed-target continuation scoring remains unsupported.
- Define ProjectionBundleV1 / artifact chain:
  - ProjectionPlan
  - BudgetWitness
  - MaterializedContext
  - MetricBridgeWitness
  - CounterfactualReplayWitness
  - ReprojectionWitness
  - ClaimLedger
- Define weak model-adjudicated labels and their bias controls.
- Define sufficiency / abstention regime labels.
- Define reprojection witness and before/after controlled replay fields.
- Define fail-closed claim ledger rules.

Forbidden:
- Treating artifacts as validation by themselves.
- Treating judge output as gold.
- Treating generated-token logprobs as fixed-target NLL.

Create:
- `docs/reviews/PAPER-REV-3-methods-backend-artifact-review.md`

Checks:
```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Done condition:
- Methods states capability boundary and claim ledger unambiguously.
- No evidence artifact changes.
- No claim upgrade introduced.
