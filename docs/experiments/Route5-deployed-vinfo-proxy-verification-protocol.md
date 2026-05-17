# Route 5 Fixed Deployed-model Logloss Proxy Verification Protocol

Status: protocol freeze only
Claim status: `no_claim_upgrade`

Route 5 freezes a scoped fixed deployed-model/logloss proxy protocol. It does
not claim true deployed V-information verification. It separates three concepts
that must remain distinct in all reports.

## Concept Separation

Formal V-information is a theoretical predictive-family quantity. It requires a
declared predictive family and an empirical or theoretical argument about the
family optimum.

Fixed deployed-model logloss proxy is an operational proxy measured with a
specific model snapshot, prompt/materialization policy, target representation,
and scoring loss. It can support only a scoped proxy claim after stability
diagnostics and review.

Operational utility is task outcome or support utility. It can be useful without
supporting either formal V-information or a fixed-model logloss proxy.

## Scoring Contract

Route 5 must predeclare:

- provider and model family;
- model name and version or snapshot when available;
- endpoint type;
- tokenizer/logprob behavior;
- scoring loss;
- target representation;
- materialization policy;
- decoding policy;
- retry and failure policy;
- contamination policy;
- exact row-key binding to Route 4 rows.

The primary loss is token-level negative log likelihood for the declared target
under the fixed materialized context. Any generation-based metric is secondary
unless separately predeclared.

## Materialization Policy

Materialization must be deterministic:

- fixed packet ordering;
- source boundaries preserved;
- stable question or claim formatting;
- stable target formatting;
- no hidden chain-of-thought or provider-specific non-deterministic mode;
- content hashes for every materialized context.

## Stability Diagnostics

Before any `vinfo_proxy_supported_candidate` status is considered, Route 5 must
report:

- repeated-score determinism on a bounded sample;
- prompt-format sensitivity;
- materialization-order sensitivity;
- model-snapshot drift check;
- tokenization or target-format sensitivity;
- budget sensitivity;
- endpoint logprob availability;
- contamination audit;
- out-of-distribution warning flags.

## Candidate Conditions

Route 5 can produce a future:

```text
vinfo_proxy_supported_candidate
```

only if:

- Route 4 has produced a reviewed metric-bridge candidate or compatible rows;
- fixed-model logloss scoring is stable under the predeclared diagnostics;
- proxy-drift checks do not fail;
- target representation is stable;
- negative controls fail;
- independent review accepts the scoped interpretation.

This candidate is scoped to the fixed deployed-model/logloss protocol. It is not
true deployed V-information verification.

## Wording Limits

Allowed future wording after gates and review:

```text
The fixed deployed-model/logloss proxy is supported for the declared model,
target representation, materialization policy, and benchmark strata.
```

Denied active wording:

- true deployed V-information verification;
- unscoped `vinfo_proxy_supported`;
- generic V-information support from operational utility;
- model-agnostic proxy support;
- proof that any production deployment will preserve the proxy.

## Stop Conditions

Stop Route 5 if:

- logprobs are unavailable or unstable;
- target tokenization changes the measured quantity;
- model snapshot cannot be pinned or documented;
- materialization sensitivity exceeds the predeclared tolerance;
- Route 4-compatible row keys are unavailable;
- a report collapses formal V-information, fixed-model logloss proxy, and
  operational utility into a single claim.
