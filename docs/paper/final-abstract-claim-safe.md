# Final Abstract Draft: Claim-Safe

Status: POST-8 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

We study dispatch-time evidence selection for context projection in live-agent
LLM systems under a formal V-information motivation and deployed live-API
constraints. The paper presents a fail-closed, replayable, claim-gated
operational audit framework for selecting and evaluating evidence under token
budgets. The framework separates formal objectives, backend capability,
operational replay, weak-evidence diagnostics, and artifact replayability.
Because the supported live API exposes generated-token chat logprobs rather
than fixed-target teacher-forced NLL or fixed-target continuation scoring, we
do not relabel those logprobs as target-side scores or treat constrained label
generation as metric evidence. The empirical package is therefore
intentionally scoped: it reports operational replay under named conditions,
replayable artifact interfaces, sufficiency and abstention diagnostics,
reprojection witnesses, extraction-risk audit, and model-adjudicated weak
candidate evidence only. The submission remains
`operational_utility_only/no_claim_upgrade`: it asserts no human/external
measurement claim, formal proxy bridge, selection-quality dominance, Route 5
unlock, or Route 8 unlock.
