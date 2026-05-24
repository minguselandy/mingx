# Sufficiency Abstention Reprojection Prompt v1

Classify whether the projected evidence is sufficient for the answer, whether the system should abstain, and whether the item should become a reprojection candidate.

Claim boundary: `sufficiency_abstention_diagnostic_only` under `operational_utility_only/no_claim_upgrade`.

This is candidate operational evidence only, not human/external gold and not measurement validation. Route 5 locked: true. Route 8 locked: true.

Allowed regime labels:
- sufficient_kept
- sufficient_dropped
- insufficient_and_answered
- insufficient_and_abstained

Allowed trigger labels:
- sufficient_dropped
- insufficient_and_answered
- unknown_due_to_missing_context
- hallucination_risk

Return strict JSON with parsed labels, missing evidence types, confidence bucket, token counts, and compact rationale. Do not include provider body text or hidden chain-of-thought.
