# Final Submission Nonclaims

Status: PAPER-REV-5 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document is the reviewer-facing index of claims the submission does not make. It does not introduce new evidence, rerun POST-LAPI experiments, run live API calls, create labels, store raw API responses, unlock Route 5, unlock Route 8, or upgrade the paper claim.

The present evidence is operational rather than validating. The contribution is a replayable, claim-gated operational audit framework for dispatch-time evidence projection under live-API constraints.

Reviewer response bank: `docs/paper/final-reviewer-response-bank.md`.

## Denied Measurement and Backend Claims

- No fixed-target teacher-forced NLL.
- No fixed-target continuation scoring.
- Generated-token logprobs are output-side diagnostics only.
- No metric bridge support.
- No calibrated proxy support.
- No V-information proxy support.
- No `calibrated_proxy_supported`.
- No `vinfo_proxy_supported`.
- No human/external gold validation.
- No measurement validation.
- No human-validated extraction measurement.
- No paper-grade evidence or paper evidence.

## Denied Selector and Route Claims

- No selector superiority.
- No global selector superiority.
- No deployed V-information verification.
- No Route 5 unlock.
- No Route 8 unlock.
- No claim upgrade beyond `operational_utility_only/no_claim_upgrade`.

## Evidence-Scope Boundaries

| evidence source | allowed reading | denied reading |
|---|---|---|
| Generated-token chat logprobs | output-side confidence diagnostics only | fixed-target teacher-forced NLL or fixed-target continuation scoring |
| POST-3 judge stability | weak model-adjudicated diagnostics only | human validation, measurement validation, or calibrated judge evidence |
| POST-4 sufficiency / abstention | sufficiency-abstention diagnostics only | truth validation, human-calibrated abstention, or measurement validation |
| POST-5 reprojection witness | candidate operational evidence only | validated repair, truth correction guarantee, or selector superiority |
| POST-6 matched-budget operational replay | scoped operational replay only under named datasets, budgets, baselines, metrics, and materialization/evaluator regime | selector superiority, global selector superiority, or metric bridge support |
| POST-7 extraction quality audit | model-adjudicated extraction-risk diagnostics only | human-validated extraction measurement, measurement validation, selector validity, or theorem transfer to runtime representations |
| Artifact hygiene and evidence freeze | replayable artifact evidence and storage-policy hygiene only | new experiment, new live API evidence, raw response storage, or stronger empirical claim |

## Locks

- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: false.
- Human labels present: false.
- Metric bridge present: false.
- Claim upgrade introduced: false.
