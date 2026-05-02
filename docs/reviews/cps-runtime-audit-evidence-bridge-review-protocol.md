# CPS Runtime-Audit Evidence Bridge：Review 审查协议

建议仓库内路径：

```text
active development repo:
C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev

final original repo / sync target:
C:\Users\Mingx\Documents\mx-codex\mingx

suggested file path in repo:
docs/reviews/cps-runtime-audit-evidence-bridge-review-protocol.md
```

## 1. 审查目的

本协议用于审查 P10 之后的 CPS runtime-audit evidence bridge 开发工作，确保每个 phase：

- 只推进被批准的工程目标；
- 不越过论文 claim boundary；
- 不把 engineering success 写成 scientific validation；
- 不绕过 P04/P09 的 operator-required 状态；
- 不从 synthetic benchmark 推断 deployed V-information submodularity；
- 保持 artifact、hash、replay、claim gate 的可审计性。

核心审查原则：

```text
Evidence before claims.
Fail closed on missing validation evidence.
Engineering compatibility is not scientific validation.
Synthetic structure is not deployed theory certification.
```

## 2. Review status taxonomy

每个 phase review 必须给出以下状态之一：

| Status | Meaning |
|---|---|
| `ACCEPT` | scope 完成，测试通过，claim boundary preserved |
| `ACCEPT_WITH_NOTES` | 可接受，但有明确 non-blocking limitations |
| `REVISE` | 需要修改后再审查 |
| `BLOCKED_OPERATOR_REQUIRED` | 需要人工、live、外部系统或科学闭环操作；代码不能解除 |
| `REJECT` | 方向错误、破坏边界、引入不可接受风险 |

禁止使用模糊状态，例如：

```text
mostly okay
probably validated
seems integrated
scientifically promising enough
```

## 3. Universal review gates

所有 phase 都必须通过以下通用 gate。

### 3.1 Repository gate

Reviewer must confirm:

- development happened in `mingx-dev`
- original `mingx` was not modified unless sync was explicitly requested
- no unrelated dirty tracked files were mixed in
- no stash was applied/popped/dropped unless explicitly instructed
- no `reference/` files were modified, staged, imported, executed, or copied
- untracked baseline paths were not accidentally committed

Pre-flight commands:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev

git status --short
git branch --show-current
git log --oneline -8
```

If the phase includes final sync, also check:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\mingx

git status --short
git branch --show-current
git log --oneline -8
```

### 3.2 Scope gate

Reviewer must confirm:

- changed files match the approved phase scope
- no unrelated refactor was introduced
- no unrelated dependency was added
- no live API path was introduced
- no external SDK import was added unless explicitly allowed
- no automatic runtime integration was added for P09
- no live cohort path was run for P04

### 3.3 Claim gate

Reviewer must confirm the phase does not claim:

```text
measurement_validated
scientific validation
human-validated measurement
fresh metric bridge, unless evidence exists
deployed V-information submodularity
runtime integration complete
P04 complete
P09 complete
```

Reviewer must confirm the phase preserves:

```text
P04: deferred/operator-required
P09: BLOCKED_OPERATOR_REQUIRED
measurement_validated: not claimed
```

### 3.4 Determinism gate

Reviewer must confirm deterministic behavior where relevant:

- stable JSON serialization where required
- stable hash generation where required
- stable output ordering where required
- no timestamps unless explicitly part of an auditable fixture
- no random numbers unless seeded and justified
- no UUID generation for deterministic artifacts
- no network calls
- no live external dependency

### 3.5 Artifact gate

For artifact-producing phases, reviewer must confirm:

- required artifact files are produced
- artifact counts are included in summary
- missing artifacts fail closed
- missing `projection_bundles` fails closed when required
- `MetricBridgeWitness` remains conservative unless validated evidence exists
- output claim level is no higher than allowed

### 3.6 Test gate

Reviewer must confirm:

- phase-specific tests exist
- existing relevant tests still pass
- tests cover fail-closed behavior
- tests cover negative/conflict cases
- tests do not require network
- tests do not require external SDKs
- optional dependency tests remain graceful when dependencies are missing

Baseline validation commands:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Recommended regression set:

```powershell
pytest tests/test_projection_bundle_v1.py -q
pytest tests/test_provider_adapters.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_selector_optional_adapters.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
pytest tests/test_projection_artifacts.py -q
```

Use phase-specific tests in addition to the baseline.

## 4. Review workflow

### Step 1 — Identify phase and branch

Record:

```text
phase:
branch:
commit hash:
base branch:
dev repo path:
original repo touched: yes/no
```

### Step 2 — Inspect status

Run:

```powershell
git status --short
git diff --stat HEAD~1..HEAD
git diff --name-only HEAD~1..HEAD
```

If multiple commits are under review:

```powershell
git log --oneline <base>..HEAD
git diff --stat <base>..HEAD
git diff --name-only <base>..HEAD
```

### Step 3 — Inspect changed files

Reviewer must check:

- public API changes
- schema changes
- docs claim language
- tests for failure modes
- imports and dependencies
- path access to `reference/`
- network or SDK usage
- claim-level changes

### Step 4 — Run validation

Run required validation commands and record exact results.

If tests are skipped, record why:

```text
Skipped tests:
- test name / file:
- reason:
- acceptable: yes/no
```

### Step 5 — Claim boundary audit

Search for risky claim terms:

```powershell
git grep -n "measurement_validated\|scientific validation\|V-information\|submodularity\|certified\|runtime integrated\|P04\|P09"
```

The presence of these terms is not automatically wrong, but reviewer must ensure they are used with correct boundaries.

Reject or revise if docs/code imply:

- synthetic success validates deployed theory
- engineering smoke validates measurement
- P04/P09 are complete
- human validation exists when labels/kappa are absent
- stale/missing bridge still allows validation-level claim

### Step 6 — Decision

Use the review decision template in Section 9.

## 5. Phase-specific review checklists

### P10 — Provider Candidate Normalizer

Expected status:

```text
ACCEPTED / HELD FOR MILESTONE PACKAGE
```

Review checklist:

- `candidate_id` ↔ `item_id` aliasing works
- `content` ↔ `text` aliasing works
- `token_cost` ↔ `token_estimate` aliasing works
- input object is not mutated
- conflicts fail closed with `ValueError`
- missing ID fails closed
- missing content/text fails closed
- token aliases require integer values
- bool token values fail closed
- pool normalization preserves order
- exported through `cps/providers/__init__.py`
- docs say engineering compatibility only
- no selector/materializer behavior silently changed

Allowed claim:

```text
engineering_compatibility_only
```

Forbidden claim:

```text
measurement_validated
runtime integrated
scientific validation
```

---

### P11 — Provider-to-Selector Offline Smoke Path

Review checklist:

- fake Graphiti-style provider candidate path exists
- fake LangExtract-style provider candidate path exists
- candidates pass through normalizer
- normalized candidates have selector/materializer-compatible aliases
- dry-run projection plan is produced
- budget witness is produced
- materialized context is produced
- conservative metric bridge witness is produced
- ProjectionBundleV1 is produced
- artifact completeness logic is exercised
- summary reports `engineering_smoke_only`
- no network calls
- no external SDK imports
- no `reference/` access
- no live cohort
- no runtime integration

Allowed claim:

```text
engineering_smoke_only
```

Forbidden claim:

```text
measurement_validated
Vinfo_proxy_certified
deployed_submodularity_certified
runtime_integrated
```

---

### P12 — Evidence Ledger and Claim Gate Report

Review checklist:

- evidence ledger schema is deterministic
- artifact counts are reported
- missing artifacts are reported
- `projection_bundles` coverage is reported
- metric bridge status is reported
- contamination status is reported
- human labels status is reported
- kappa status is reported
- P04/P09 status is reported
- allowed claim level is explicit
- denied claim reasons are explicit
- JSON and Markdown outputs are deterministic enough for replay
- missing labels block `measurement_validated`
- missing kappa blocks `measurement_validated`
- engineering-only evidence does not validate science

Expected reason codes include:

```text
missing_human_labels
missing_kappa
missing_metric_bridge
stale_metric_bridge
contamination_failed
synthetic_only
operator_required_phase
runtime_integration_missing
artifact_incomplete
projection_bundle_missing
engineering_only
```

Allowed claim:

```text
replayable_artifact_evidence or lower
```

---

### P13 — Metric Bridge Gate Hardening

Review checklist:

- explicit gate evaluator exists
- fail-closed logic is tested
- missing labels => not `measurement_validated`
- missing kappa => not `measurement_validated`
- contamination failure => `pilot_only`
- stale bridge => `operational_utility_only` or `ambiguous`
- missing bridge => `operational_utility_only` or `ambiguous`
- synthetic-only => `synthetic_structural_only`
- engineering-only => not scientific validation
- gate produces reason codes
- docs describe limitations
- no automatic upgrade to validation-level claim

Allowed claim:

```text
claim-gate hardening only
```

---

### P14 — Proxy-Regime Certification Matrix

Review checklist:

- regime matrix includes redundancy-dominated case
- regime matrix includes pairwise-synergy case
- regime matrix includes higher-order / prerequisite case
- expected behavior is documented
- observed diagnostic behavior is documented
- failure modes are documented
- claim denied reasons are documented
- output is deterministic
- matrix title/language does not imply deployed validation

Allowed claim:

```text
synthetic_structural_only
```

Forbidden claim:

```text
deployed V-information submodularity certified
measurement_validated
```

---

### P15 — Replay Evidence Package Builder

Review checklist:

- deterministic replay package builder exists
- manifest generated
- artifact counts generated
- bundle hashes generated
- claim gate report included
- Markdown summary generated
- missing required artifacts fail closed
- missing projection bundles fail closed
- no live artifacts generated
- no claim gate relaxation

Allowed claim:

```text
replayable_artifact_evidence
```

---

### P16 — Paper Evidence Summary Builder

Review checklist:

- manuscript-facing JSON summary generated
- manuscript-facing Markdown summary generated
- artifact schema summarized
- claim ladder summarized
- proxy regime matrix summarized
- replay evidence summarized
- missing labels/kappa limitations explicit
- P04/P09 blocked status explicit
- wording avoids scientific overclaim

Allowed claim:

```text
manuscript_evidence_summary_only
```

---

### P17 — Phase 1 Scientific Closure Preparation

Review checklist:

- label protocol documented
- annotator requirements documented
- kappa calculation plan documented
- contamination audit documented
- metric bridge freshness criteria documented
- decision sheet template documented
- failure handling documented
- still operator-required
- no live run performed
- no measurement validation claimed

Allowed claim:

```text
scientific_closure_protocol_prepared
```

Status should remain:

```text
BLOCKED_OPERATOR_REQUIRED until operator execution is completed and reviewed
```

---

### P18 — Runtime Adapter Prototype v0

Review checklist:

- dry-run adapter contract exists
- fake/local runtime events only
- ProjectionRequest/ProjectionResponse contract is deterministic
- ProjectionBundle export path is deterministic
- no external runtime SDK imported
- no network calls
- no production integration
- P09 remains blocked unless explicitly reviewed as operator-approved

Allowed claim:

```text
runtime_adapter_contract_dry_run_only
```

Forbidden claim:

```text
runtime integration complete
production runtime validated
```

## 6. Documentation review rules

Docs must use conservative wording.

Preferred wording:

```text
engineering compatibility layer
offline smoke path
synthetic structural diagnostic
proxy-regime evidence
conservative claim gate
measurement validation not claimed
operator-required
```

Risky wording requiring review:

```text
validated
certified
proven
guaranteed
scientific validation
runtime integrated
V-information certified
submodularity certified
```

Acceptable only when the sentence explicitly denies overclaim, for example:

```text
Synthetic benchmark success does not certify deployed V-information submodularity.
```

## 7. Dependency and environment review

Reviewer must inspect imports in changed files.

Forbidden unless explicitly approved:

```text
Graphiti SDK
LangExtract SDK
submodlib outside optional adapter boundary
OR-Tools outside optional adapter boundary
Langfuse SDK
OTel SDK
Phoenix SDK
network clients
reference/ imports
```

Allowed:

- Python standard library
- existing project modules
- optional adapter imports already guarded by graceful unavailable behavior
- test-local fake objects

## 8. Artifact review rules

For each artifact-producing phase, reviewer must check:

```text
artifact root:
file list:
summary file:
required counts:
projection bundle count:
metric bridge witness count:
claim level:
reason codes:
hashes stable: yes/no/not applicable
```

Artifact failures requiring `REVISE` or `REJECT`:

- artifact summary says complete while required files are missing
- projection bundles missing but completeness passes
- metric bridge missing but claim remains high
- contaminated run not downgraded
- missing labels/kappa but `measurement_validated` appears
- synthetic-only evidence described as deployed validation

## 9. Review decision template

Use this template at the end of every phase review.

```markdown
# Phase Review Decision

## Phase

- Phase:
- Branch:
- Commit(s):
- Review date:
- Reviewed repo:

## Decision

Status: ACCEPT | ACCEPT_WITH_NOTES | REVISE | BLOCKED_OPERATOR_REQUIRED | REJECT

## Scope check

- Expected scope:
- Actual changed files:
- Out-of-scope changes: none / list

## Validation

Commands run:

```text
<commands>
```

Results:

```text
<results>
```

Skipped tests:

```text
<none or list with reason>
```

## Claim boundary

- P04 remains deferred/operator-required: yes/no
- P09 remains BLOCKED_OPERATOR_REQUIRED: yes/no
- measurement_validated claimed: yes/no
- scientific validation claimed: yes/no
- deployed V-information submodularity certified: yes/no
- engineering success reported as scientific validation: yes/no

Allowed claim level:

```text
<claim level>
```

Denied claim reasons:

```text
<reason codes>
```

## Artifact review

- Required artifacts present: yes/no/not applicable
- ProjectionBundleV1 coverage: pass/fail/not applicable
- MetricBridgeWitness claim level conservative: yes/no/not applicable
- Completeness fail-closed behavior tested: yes/no/not applicable

## Determinism review

- Stable output order: yes/no/not applicable
- Stable hashes: yes/no/not applicable
- No timestamps/UUID/randomness: yes/no/not applicable
- No network/API calls: yes/no
- No reference/ access: yes/no

## Notes

Known non-blocking limitations:

```text
<notes>
```

Required follow-up:

```text
<follow-up>
```
```

## 10. Milestone review template

Use after P10–P13, P14–P16, or P17–P18 packages.

```markdown
# Milestone Review Decision

## Milestone

- Name:
- Branch:
- Commit range:
- Included phases:

## Decision

Status: ACCEPT | ACCEPT_WITH_NOTES | REVISE | BLOCKED_OPERATOR_REQUIRED | REJECT

## Phase decisions

| Phase | Status | Commit | Notes |
|---|---|---:|---|
| P10 |  |  |  |
| P11 |  |  |  |
| P12 |  |  |  |
| P13 |  |  |  |

## Validation summary

```text
<commands and results>
```

## Claim boundary summary

- Highest allowed claim level:
- `measurement_validated`: claimed / not claimed
- P04: status
- P09: status
- synthetic success used for deployed certification: yes/no
- engineering success used for scientific validation: yes/no

## Evidence summary

- Artifact completeness:
- Bundle hash coverage:
- Claim gate report:
- Metric bridge status:
- Replay evidence:
- Proxy regime evidence:

## Sync recommendation

- Sync to original repo now: yes/no
- Recommended original repo branch:
- Recommended PR title:
- Special sync warnings:
```

## 11. Sync review protocol

Only run this section when explicitly syncing accepted milestone work to the original repo.

Target repo:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\mingx
```

Pre-flight:

```powershell
git status --short
git switch main
git pull --ff-only origin main
```

Create review branch:

```powershell
git switch -c codex/sync-runtime-audit-evidence-bridge
```

Fetch milestone branch:

```powershell
git fetch "C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev" codex/milestone-runtime-audit-evidence-bridge:refs/remotes/mingx-dev/runtime-audit-evidence-bridge
```

Reviewer must ensure:

- only accepted commits are synced
- no dev-only untracked baseline paths are included
- no stash is touched
- `reference/` is not included
- sync branch validates independently
- PR body preserves claim boundaries

Post-sync validation must include:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

plus all phase-specific tests.

## 12. PR body review requirements

Every milestone PR body must include:

```markdown
## Summary

<engineering summary>

## Boundary

This is engineering / proxy / replay evidence only as applicable.
It does not claim measurement validation.
It does not certify deployed V-information submodularity.
It does not unblock P04 or P09.

## Validation

<commands and results>

## Claim Gate

- P04:
- P09:
- measurement_validated:
- highest allowed claim:
- denied claim reasons:

## Changed files

<file list>
```

Reject or revise PR text if it overclaims.

## 13. Immediate next review target

Next phase to review:

```text
P11 Provider-to-Selector Offline Smoke Path
```

Expected P11 decision if successful:

```text
P11 ACCEPT
claim: engineering_smoke_only
measurement_validated: not claimed
P04/P09: unchanged blocked/operator-required
```

Expected P11 non-blocking limitation:

```text
Offline smoke path uses fake/local provider candidates and does not constitute external runtime integration or scientific validation.
```
