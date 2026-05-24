# PAPER-REV-8 Independent Final Claim Audit

Status: complete
Verdict: ACCEPT_WITH_NOTES
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This audit reviews the PAPER-REV package after PAPER-REV-1 through PAPER-REV-7, with primary attention on:

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/paper/final-reviewer-response-bank.md`

No live API calls, new experiments, POST-3 through POST-7 reruns, raw artifact edits, or route unlocks were performed.

## Required Scan Status

The requested Unix `grep ... || true` command could not be executed exactly in this Windows PowerShell environment: `||` is not accepted by the shell, and `grep` is not installed. I therefore ran the equivalent `rg` scan with the same forbidden terms over `docs`, `tests`, `scripts`, and `cps`, excluding `.git`, `.codex`, `mingx_*_codex_goals`, `docs/goals`, and generated scratch leftovers.

Equivalent active scan:

```text
rg -n --hidden --glob '!**/.git/**' --glob '!**/.codex/**' --glob '!**/mingx_*_codex_goals/**' --glob '!docs/goals/**' --glob '!tests/.tmp/**' -e "teacher-forced NLL support|fixed-target continuation scoring support|metric bridge support|calibrated_proxy_supported|vinfo_proxy_supported|measurement validation|human/external gold validation|paper-grade evidence|selector superiority|global selector superiority|Route 5 unlock|Route 8 unlock" docs tests scripts cps
```

Result: 2,057 contextual matches across 390 active files. The matches are expected in claim-gate constants, false/locked status rows, denied-claim lists, guardrail tests, scripts that emit non-claim summaries, and historical docs. The review-target scan found one legacy positive-looking `vinfo_proxy_supported` maximum-claim row in `docs/paper/P44-manuscript-evidence-integration-plan.md`; it was corrected to `operational_utility_only`.

Post-correction explicit true/unlocked scan:

```text
rg -n -i -e "\|\s*(calibrated_proxy_supported|vinfo_proxy_supported)\s*\|\s*true|Route 5:\s*unlocked|Route 8:\s*unlocked|Route 5\s*/\s*Route 8:\s*unlocked|raw API responses stored:\s*true|raw_response_stored\s*\|\s*true|human/external gold validation:\s*true|measurement validation:\s*true" docs/archive/context_projection_fixed_v12.md docs/reviews/reviewer-defense-live-api-operational-paper.md docs/paper
```

Result: zero matches.

## Correction Applied

`docs/paper/P44-manuscript-evidence-integration-plan.md` contained legacy rows that treated synthetic-only evidence as `vinfo_proxy_supported`. Those rows are now downgraded to `operational_utility_only`. This was a docs-only claim-boundary correction and did not add manuscript evidence or change artifacts.

## Audit Checklist

| requirement | status | evidence |
|---|---|---|
| No measurement validation claim | PASS | Denied in `context_projection_fixed_v12.md` lines 481, 489, 501; response bank lines 28, 54, 62, 78. |
| No human/external gold validation claim | PASS | Denied in `context_projection_fixed_v12.md` lines 489, 501; response bank line 94. |
| No fixed-target NLL claim | PASS | Backend limitation stated in reviewer defense lines 14-16 and response bank lines 10-14. |
| No teacher-forced scoring claim | PASS | Denied in `context_projection_fixed_v12.md` line 501 and response bank line 68. |
| No metric bridge claim | PASS | Denied in `context_projection_fixed_v12.md` lines 481, 489, 501; response bank lines 14, 22, 46, 54, 62. |
| No `calibrated_proxy_supported` claim | PASS | Explicit true-flag scan returned zero matches; `context_projection_fixed_v12.md` line 501 denies the flag. |
| No `vinfo_proxy_supported` claim | PASS | Legacy `P44` rows corrected; explicit true-flag scan returned zero matches; response bank line 22 denies the flag. |
| No paper-grade evidence claim | PASS | Denied in `context_projection_fixed_v12.md` line 489 and response bank lines 38, 62, 78. |
| No selector superiority claim | PASS | Denied in reviewer defense lines 26-28, 69, 85-86 and response bank lines 38, 46, 62. |
| No global selector superiority claim | PASS | Denied in reviewer defense line 86 and response bank lines 38, 46, 62. |
| No Route 5 / Route 8 unlock | PASS | `context_projection_fixed_v12.md` lines 489 and 493-499 keep both locked; response bank lines 91-92 keep both locked. |
| Raw API responses not stored | PASS | Reviewer defense line 48 and response bank lines 74-78 and 93 state raw responses are not stored / false. |
| Judge labels weak only | PASS | `context_projection_fixed_v12.md` lines 487, 494 and reviewer defense line 24 keep judge/model labels weak and candidate-only. |
| Operational replay scoped only | PASS | `context_projection_fixed_v12.md` lines 487, 497 and response bank lines 42-46 scope replay to named datasets, budgets, baselines, metrics, and regime. |
| Extraction audit diagnostic only | PASS | `context_projection_fixed_v12.md` lines 487, 498 and reviewer defense line 60 keep extraction as extraction-risk diagnostics only. |
| Reprojection operational witness only | PASS | `context_projection_fixed_v12.md` lines 487, 496 and `docs/paper/v12-evidence-ledger.md` line 92 describe reprojection as operational omitted-evidence witness/candidate evidence only. |

## Verdict

ACCEPT_WITH_NOTES. The package now satisfies the locked claim ceiling after the single docs-only `P44` downgrade. The note is limited to environment and audit trail: exact Unix `grep` was unavailable, so equivalent `rg` scans were used and recorded.
