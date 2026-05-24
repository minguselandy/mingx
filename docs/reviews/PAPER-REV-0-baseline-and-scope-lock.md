# PAPER-REV-0 Baseline And Scope Lock

Status: final paper revision baseline and manuscript-scope lock
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This review locks the PAPER-REV-0 baseline for paper-only final manuscript
revision. No live API calls are authorized for this revision path, no new
experiments are recommended, and the POST-LAPI evidence package is frozen for
claim-safe manuscript synthesis.

## Baseline

| field | value |
|---|---|
| Branch | `codex/integrated-validation-workbench` |
| Local HEAD | `ead306ba97fe9a85a881f1b0e931badf1edf2278` |
| Remote ref | `origin/codex/integrated-validation-workbench` |
| Remote HEAD | `ead306ba97fe9a85a881f1b0e931badf1edf2278` |
| Remote alignment | aligned |
| Tracked worktree | clean |
| Staged files | none |
| SUB-4 decision | `NO_MORE_EXPERIMENTS_RECOMMENDED` |
| Handoff verdict | `ACCEPT_WITH_NOTES` |

Excluded untracked leftovers remain out of scope and unstaged. They include
Beta, Route4D, Route6C, WS0 / WS1, teacher-forced backend, EPF WS6 nested
ledger, old goal-pack, and unrelated excluded leftovers.

## Revision Scope

The final revision is paper-only. It may revise wording, tables, captions,
claim ledgers, artifact indexes, limitations, and reviewer-defense text, but it
must not start experiments, rerun POST-3 through POST-7, scale silver labels,
unlock Route 5, unlock Route 8, store raw API responses, or introduce any claim
upgrade.

The evidence package is frozen. Existing POST-LAPI run-pilot artifacts may be
referenced only as already-produced, normalized, claim-bounded evidence. SUB-0
through SUB-5 synthesis artifacts report zero live API calls during synthesis.

## Evidence Inventory

| package | inspected source | rows / records / calls | gate | allowed use |
|---|---|---:|---|---|
| POST-3 judge stability | `artifacts/experiments/post_lapi_judge_stability/` | 240 normalized rows / 240 prior live API calls | `weak_evidence_candidate_ready` | weak model-adjudicated diagnostics only |
| POST-4 sufficiency / abstention | `artifacts/experiments/post_lapi_sufficiency_abstention/` | 50 normalized rows / 50 final artifact calls | `sufficiency_abstention_candidate_ready` | sufficiency / abstention diagnostic only |
| POST-5 reprojection witness | `artifacts/experiments/post_lapi_reprojection_witness/` | 26 normalized rows / 26 prior live API calls | `reprojection_witness_candidate_ready` | operational reprojection witness only |
| POST-6 operational replay | `artifacts/experiments/post_lapi_operational_replay/` | 2,000 replay records / 200 candidate pools / 0 live API calls | `post6_operational_replay_completed` | scoped operational replay under matched budgets only |
| POST-7 extraction audit | `artifacts/experiments/post_lapi_extraction_quality_audit/` | 100 extraction audit records / 100 prior live API calls | `post7_extraction_quality_audit_completed` | model-adjudicated extraction-risk diagnostics only |
| SUB-0 evidence freeze | `artifacts/audits/post_lapi_evidence_freeze/` | 27 JSON files / 5 JSONL files / 2,416 JSONL rows | SUB-0 scans passed | artifact hygiene and storage-policy evidence only |

All inspected gate reports retain `operational_utility_only/no_claim_upgrade`,
`raw_response_stored: false`, Route 5 locked, Route 8 locked, and no positive
measurement-validation or selector-superiority claim.

## Allowed Claims

- Operational replay evidence.
- Candidate operational evidence.
- Model-adjudicated weak evidence.
- Sufficiency / abstention diagnostic.
- Operational reprojection witness.
- Extraction-risk diagnostic.
- Replayable artifact evidence.
- Fail-closed bridge audit.
- Scoped operational improvement under matched budgets.

## Denied Claims

- Measurement validation.
- Human/external gold validation.
- Fixed-target teacher-forced NLL support.
- Fixed-target continuation scoring support.
- Teacher-forced scoring support.
- Metric bridge support.
- `calibrated_proxy_supported`.
- `vinfo_proxy_supported`.
- Paper-grade evidence.
- Paper evidence.
- Deployed V-information verification.
- Selector superiority.
- Global selector superiority.
- Route 5 unlock.
- Route 8 unlock.

## Checks

| command | result |
|---|---|
| `git status --short --untracked-files=all` | completed; tracked worktree clean, staged files empty, excluded untracked leftovers present |
| `git branch --show-current` | `codex/integrated-validation-workbench` |
| `git rev-parse HEAD` | `ead306ba97fe9a85a881f1b0e931badf1edf2278` |
| `git rev-parse origin/codex/integrated-validation-workbench` | `ead306ba97fe9a85a881f1b0e931badf1edf2278` |
| `git diff --check` | passed |
| `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q` | passed: `20 passed` |
| `python -m compileall cps tests scripts` | passed |

## Lock Verdict

PAPER-REV-0 is ready for paper-only manuscript revision under the current
claim ceiling. The allowed manuscript boundary is operational utility and weak
diagnostic evidence only. No evidence artifacts were changed as part of this
scope lock, no live API calls were run, and no claim upgrade is introduced.
