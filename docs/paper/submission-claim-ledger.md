# Submission Claim Ledger

Status: POST-8 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This ledger is a paper-facing claim boundary summary. It does not run live API
calls, start experiments, create labels, store raw API responses, unlock Route
5, unlock Route 8, or upgrade claims.

## Claim Boundary

Allowed paper-facing language:

- backend-constrained operational diagnostic
- fail-closed bridge audit
- replayable artifact interface
- operational evaluation under named datasets, budgets, and baselines
- model-adjudicated weak-evidence diagnostics, when reported as weak source
- candidate operational evidence for EPF-FINAL silver labels
- extraction-risk audit configuration, not extraction measurement validation

Required stance:

- We do not relabel generated-token chat logprobs as teacher-forced NLL.
- We do not claim V-information verification.
- We do not claim measurement validation.
- The contribution is a fail-closed, replayable, claim-gated operational audit
  framework for dispatch-time evidence selection.

## Denied Claims

| claim | submission status | safe wording |
|---|---|---|
| fixed-target NLL bridge | denied | live API chat-logprob diagnostics only |
| teacher-forced NLL support | denied | generated-token confidence diagnostics only |
| metric bridge support | denied | bridge attempts failed closed or are unavailable |
| calibrated proxy support | denied | no `calibrated_proxy_supported` claim |
| V-information proxy support | denied | no `vinfo_proxy_supported` claim |
| V-information verification | denied | V-information is the formal target, not a deployed verified measure |
| measurement validation | denied | no human/external gold validation and no accepted measurement route |
| human-validated extraction measurement | denied | extraction audit remains operational risk evidence only |
| paper evidence upgrade | denied | current live-API outputs remain operational or candidate-only |
| selector superiority | denied | only scoped operational comparisons are allowed |
| global selector superiority | denied | no global superiority claim |
| Route 5 unlock | denied | Route 5 locked |
| Route 8 unlock | denied | Route 8 locked |

## Package Ledger

| package | current state | allowed use | denied boundary |
|---|---|---|---|
| Backend capability | Live API exposes generated-token chat logprobs but not fixed-target continuation scoring. | Explain backend limits and fail-closed claim gating. | No teacher-forced NLL, metric bridge support, calibrated proxy support, V-information proxy support, Route 5 unlock, or Route 8 unlock. |
| Route 2 operational replay | HotpotQA operational comparison under matched budgets and deployable baselines. | Scoped operational improvement under matched budgets. | No selector superiority, global selector superiority, metric bridge support, measurement validation, or V-information verification. |
| Artifact replay integrity | Offline replay-integrity audit and manifest checks. | Replayable artifact interface and auditability. | No scientific validation, measurement validation, paper-grade evidence, metric bridge support, or selector superiority. |
| EPF-FINAL | Candidate operational package with LLM-generated silver labels. | Candidate operational evidence package only. | No human/external gold validation, measurement validation, paper evidence, metric bridge support, Route 5 unlock, or Route 8 unlock. |
| Judge weak-evidence stability | Configured weak-source diagnostics and table template. | Model-adjudicated weak-evidence diagnostics after approved run. | No human gold, judge validation, measurement validation, paper evidence, or selector superiority. |
| Sufficiency and abstention | Configured diagnostic regime. | Sufficiency and abstention diagnostic after approved run. | No truth validation, human-calibrated abstention, measurement validation, or paper evidence. |
| Reprojection witness | Configured witness repair/replay surface. | Replayable artifact witness after approved controlled replay. | No validated repair, truth correction guarantee, metric bridge support, or selector superiority. |
| Extraction quality audit | Configured M* -> M extraction-risk audit. | Operational extraction-risk audit after approved run. | No human-validated extraction measurement, theorem transfer to M*, end-to-end validation, or measurement validation. |

## Locks

Route 5 locked: yes

Route 8 locked: yes

Raw API responses stored: no

Claim upgrade introduced: no
