# PAPER-RS V12 Live-API Operational Restructuring Review

date: 2026-05-22
verdict: ACCEPT_WITH_NOTES
blocked: false
requires_operator: false
claim_status: `operational_utility_only/no_claim_upgrade`
route5_locked: true
route8_locked: true

## Scope

PAPER-RS restructures the v12 manuscript and paper-facing docs from any implied
validation-grade V-information proxy story into a claim-safe, V-information
anchored, live-agent operational diagnostic paper. This review creates no new
experiments, operator inputs, live API calls, raw responses, raw dataset mirrors,
runtime behavior, claim ledger upgrade, Route 5 unlock, or Route 8 unlock.

## Files Changed

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper-alignment-v12.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/paper/v12-manuscript-integration-checklist.md`
- `docs/paper/v12-live-api-operational-paper-claim-table.md`
- `docs/experiments/EPF-final-live-api-silver-label-candidate-package.md`
- `docs/reviews/PAPER-RS-v12-live-api-operational-restructuring-review.md`

## Claim Boundary

Allowed current claim:

```text
operational_utility_only/no_claim_upgrade
```

Denied current claims:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- metric bridge support
- paper-grade validation evidence
- teacher-forced NLL support
- fixed-target continuation scoring support
- human/external gold validation
- selector superiority
- global selector superiority
- deployed V-information verification
- Route 5 unlock
- Route 8 unlock

## Evidence-State Review

- Manuscript abstract, introduction, bridge statement, evidence organization,
  EPF-FINAL section, related work, limitations, and conclusion preserve
  operational-only framing.
- EPF-FINAL is represented as accepted with notes for candidate operational use:
  8 LLM-generated silver-label rows over 2 parent samples, no raw API responses,
  no human/external gold labels, and no measurement or metric-bridge claim.
- Evidence ledger and checklist now include Route 2 operational evidence, Route
  3/4 fail-closed bridge attempts, Route 6B model-adjudicated measurement
  candidate, Delta judge-reliability fail-closed state, Gamma operational
  expansion, LogProbe/EPN/TFS blocked diagnostic chain, and EPF-FINAL.
- The new paper claim table gives allowed and denied claims for the formal
  objective, synthetic smoke test, Route 2, Route 3, Route 4, Route 6B, Delta,
  Gamma, LogProbe/EPN/TFS, and EPF-FINAL.

## Remaining Future Evidence Routes

- Route 4 would need a separately accepted bridge candidate before any bridge
  support claim.
- Route 5 remains locked until a future fixed deployed-model/log-loss package is
  explicitly authorized and evidence-backed.
- Route 6 remains measurement-candidate only until human/external gold labels,
  kappa, contamination, and independent review gates are satisfied.
- Route 8 remains locked.
- EPF-FINAL may remain a backend-constrained operational candidate package only;
  stronger use requires a future backend/evidence path that is not present here.

## Checks Run

```text
git -c safe.directory='C:/Users/Mingx/Documents/mx-codex/agentic-codex/mingx-dev' status --short
Result: exit 0. Shows intended PAPER-RS modified docs plus pre-existing untracked leftovers; no files were staged.
```

```text
git -c safe.directory='C:/Users/Mingx/Documents/mx-codex/agentic-codex/mingx-dev' diff --check
Result: exit 0. Only LF-to-CRLF working-copy warnings were reported.
```

```text
uv run pytest tests/test_revised_framing_guardrails.py -q
Result: exit 0. 13 passed in 0.62s.
```

```text
python -m compileall cps tests
Result: exit 0. Compile traversal completed for cps and tests.
```

Targeted claim-boundary grep was run over the changed paper docs for calibrated
proxy, V-information proxy, measurement validation, metric bridge support,
teacher-forced NLL support, fixed-target continuation scoring support, global
selector superiority, Route 5 unlock, Route 8 unlock, and deployed
V-information verification. Occurrences were denied, false-valued,
operational-only, or future-scoped; no active claim upgrade was found.

## Review Notes

- Existing EPF generation artifacts still preserve their generation-time
  manifest fields. This PAPER-RS package updates paper-facing docs and the EPF
  final report to reflect the current accepted-with-notes candidate operational
  status.
- Commit, staging, push, and PR creation remain outside this review.
