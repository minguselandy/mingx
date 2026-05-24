# WS9 Candidate Evidence Package

A reviewable limited-scope candidate package was produced. Independent review is required before any claim ledger or paper upgrade.

Post-push hardening preserves the claim ceiling:
`operational_utility_only/no_claim_upgrade`. Live API execution is restricted
to the DashScope-compatible API surface with `DASHSCOPE_API_KEY` or
`QWEN_API_KEY` and an approved DashScope-compatible base URL. Generic `API_KEY`
fallbacks and local/model-hosted backend fallbacks are rejected before live
probes.
