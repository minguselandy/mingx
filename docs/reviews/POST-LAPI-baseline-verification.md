# POST-LAPI Baseline Verification

Goal ID: POST-0 / Post-merge baseline verification
Date: 2026-05-24

## Baseline State

| item | result |
|---|---|
| Branch | `codex/integrated-validation-workbench` |
| HEAD | `f38d3aa` |
| HEAD subject | `LAPI integrate live API operational paper framing` |
| origin/codex/integrated-validation-workbench | `f38d3aa` |
| origin/main contains `f38d3aa` | yes |
| Index clean | yes |
| Branch switch performed | no |

`git fetch origin` completed after the sandboxed attempt failed to write
`.git/FETCH_HEAD` with `Permission denied`. The successful fetch updated
`origin/main` from `276b422` to `b5b4b4a`.

## Untracked Leftovers Summary

Historical untracked leftovers remain isolated and were not staged, deleted,
moved, or cleaned.

| top-level path | untracked entries |
|---|---:|
| `artifacts` | 20 |
| `codex-goals` | 27 |
| `configs` | 16 |
| `cps` | 8 |
| `docs` | 21 |
| `tests` | 3 |

Known leftover families still present include Beta, Route4D, Route6C, WS0/WS1,
WS6 nested `claim_ledger.json` files, post-LAPI goal/config packs, prior LAPI
goal docs, teacher-forced evaluator leftovers, and related tests/docs.

## Checks Run

| command | result |
|---|---|
| `git status --short --untracked-files=all` | passed; untracked leftovers listed only |
| `git branch --show-current` | `codex/integrated-validation-workbench` |
| `git rev-parse --short HEAD` | `f38d3aa` |
| `git rev-parse --short origin/codex/integrated-validation-workbench` | `f38d3aa` |
| `git fetch origin` | passed after escalation for `.git/FETCH_HEAD` write access |
| `git merge-base --is-ancestor f38d3aa origin/main` | `HEAD_CONTAINED_IN_ORIGIN_MAIN=yes` |
| `git diff --check` | passed |
| `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q` | passed: 20 passed |
| `python -m compileall cps tests` | passed |
| claim-boundary grep over `docs tests cps` | completed; 1697 review hits |

The initial sandboxed pytest command failed because `uv` could not open the
user-level cache under `C:\Users\Mingx\AppData\Local\uv\cache`. The escalated
rerun of the same command passed.

## Claim-Boundary Review

Claim status remains `operational_utility_only/no_claim_upgrade`.

The claim-boundary grep returned expected hits in denied-claim tables,
historical protocol docs, code constants, and tests that assert forbidden
claims remain false or absent. The required guardrail tests passed, and no new
claim upgrade was introduced by this baseline verification report.

Current lock and storage state:

| claim flag | result |
|---|---|
| Live API calls run | no |
| New experiments run | no |
| Raw API responses stored | no |
| Claim upgrade introduced | no |
| Route 5 locked | yes |
| Route 8 locked | yes |
| Unrelated leftovers staged | no |

## Next Recommended Goal

Run `codex-goals/post-lapi/codex-goals/configure/01-artifact-replay-integrity-config.goal.md`.
