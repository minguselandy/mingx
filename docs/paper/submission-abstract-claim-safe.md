# Claim-Safe Submission Abstract

Status: SUB-3 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

We study dispatch-time evidence projection in a live-agent / live-API setting. The paper uses predictive V-information as the formal anchor for deciding which evidence should enter a worker context, but the current evidence package is operational-only: the supported live API does not expose fixed-target teacher-forced NLL or a metric bridge from dispatch-time projection to calibrated answer likelihood. We therefore present the empirical section as `Operational evaluation and weak-evidence diagnostics`.

The submission reports weak model-adjudicated diagnostics, sufficiency / abstention behavior, reprojection witness records for omitted-evidence cases, scoped operational replay under matched budgets, model-adjudicated extraction-risk audit evidence, and replayable artifact evidence with fail-closed claim gates. These artifacts make the live-API constraints, storage policy, route locks, and denied claims inspectable without treating weak operational signals as stronger evidence.

The abstract-safe claim is narrow: POST-LAPI supports a claim-gated operational audit framework for dispatch-time evidence projection. It does not establish fixed-target teacher-forced NLL, metric bridge support, V-information proxy validation, measurement validation, human/external gold validation, selector superiority, Route 5 unlock, or Route 8 unlock. The conclusion remains `operational_utility_only/no_claim_upgrade`.
