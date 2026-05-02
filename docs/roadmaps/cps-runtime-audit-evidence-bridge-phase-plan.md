# CPS Runtime-Audit Evidence Bridge：开发 Phase 规划

建议仓库内路径：

```text
active development repo:
C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev

final original repo / sync target:
C:\Users\Mingx\Documents\mx-codex\mingx

suggested file path in repo:
docs/roadmaps/cps-runtime-audit-evidence-bridge-phase-plan.md
```

## 1. 规划目的

本规划用于指导 `mingx` 项目在 P10 之后的阶段性开发。当前项目的核心目标不是扩展为通用 agent framework，而是形成面向论文的 **CPS measurement / runtime-audit scaffold**：

> Context Projection Selection in Multi-Agent Systems: Conditional Theory, Metric Bridge, and Proxy-Regime Certification

下一阶段的开发目标不是立即跑 live cohort、不是接入外部 runtime、不是宣称 scientific validation，而是把已有的工程能力组织成可审计、可复现、claim-safe 的论文证据链。

核心方向：

```text
provider candidates
  → deterministic normalization
  → offline selector/materializer-compatible path
  → ProjectionBundleV1
  → artifact completeness
  → metric bridge witness
  → conservative claim gate
  → replay / paper evidence package
```

## 2. 当前基线状态

当前已知状态：

| Phase | Status | Meaning |
|---|---:|---|
| P00 | ACCEPT | 自动化开发框架接入 |
| P01 | ACCEPT | `ProjectionBundleV1` canonical JSON / stable hash / identity validation |
| P02 | ACCEPT | cohort path projection artifact event export |
| P03 | ACCEPT | follow-up CLI build/validate package |
| P04 | BLOCKED_OPERATOR_REQUIRED | Phase 1 scientific closure runbook only；未跑 live |
| P05 | ACCEPT | deterministic synthetic regime benchmark |
| P06 | ACCEPT | optional `submodlib` selector / OR-Tools oracle adapters |
| P07 | ACCEPT | OTel / Langfuse / Phoenix dry-run exporters |
| P08 | ACCEPT | Graphiti / LangExtract-style provider adapters |
| P09 | BLOCKED_OPERATOR_REQUIRED | runtime adapter prototype plan；未做外部 runtime integration |
| P10 | ACCEPT / HELD | provider candidate normalization bridge；暂不要求立即 merge main |

P10 已完成内容：

- `cps/providers/normalizer.py`
- `normalize_candidate_payload(...)`
- `normalize_candidate_pool(...)`
- `candidate_id/content/token_cost` 与 `item_id/text/token_estimate` alias bridge
- fail-closed conflict detection
- provider adapter docs 更新
- 20 条 normalizer 测试

P10 仍然只是：

```text
engineering_compatibility_only
```

P10 不代表：

```text
measurement_validated
V-information certified
submodularity certified
metric bridge fresh
runtime integrated
P04/P09 unblocked
```

## 3. 固定 claim gate

后续所有 phase 必须遵守以下 claim gate：

| Condition | Required claim behavior |
|---|---|
| contamination failure | `pilot_only` |
| missing human labels | not `measurement_validated` |
| missing kappa | not `measurement_validated` |
| stale metric bridge | `operational_utility_only` or `ambiguous` |
| missing metric bridge | `operational_utility_only` or `ambiguous` |
| synthetic benchmark success only | not deployed V-information submodularity certification |
| engineering success only | not scientific validation |
| P04 still blocked | no Phase 1 scientific closure claim |
| P09 still blocked | no external runtime integration claim |

Recommended claim ladder:

| Level | Claim level | Meaning |
|---:|---|---|
| L0 | `engineering_compatibility_only` | Schema / field bridge / dry compatibility only |
| L1 | `engineering_smoke_only` | Offline fake path runs end-to-end |
| L2 | `replayable_artifact_evidence` | Complete deterministic artifacts and stable hashes |
| L3 | `synthetic_structural_only` | Proxy/synthetic regime diagnostics only |
| L4 | `operational_utility_only` | Limited operational metric bridge claim only |
| L5 | `measurement_validated` | Requires human labels, kappa, contamination pass, fresh bridge, and closure evidence |
| L6 | `deployed_theory_certified` | Not a current engineering target; must not be inferred from synthetic success |

## 4. Repository workflow

Active development happens in:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev
```

Final milestone sync happens later into:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\mingx
```

Development rule:

```text
Do not sync each small phase immediately.
Complete a coherent milestone package in mingx-dev first.
Then sync the accepted milestone into mingx as a review branch / PR.
```

Reference policy:

```text
reference/ is read-only design reference only.
Do not import, execute, modify, copy, or commit reference/ code.
```

Stash policy:

```text
Do not apply, pop, drop, or rewrite existing stash entries unless explicitly instructed.
```

## 5. Milestone structure

Recommended next milestone:

```text
M1: CPS Runtime-Audit Evidence Bridge
```

Theme:

```text
Provider-compatible CPS audit evidence and conservative claim gating.
```

Recommended phase package:

```text
P10 Provider Candidate Normalizer                [done / held]
P11 Provider-to-Selector Offline Smoke Path       [next]
P12 Evidence Ledger and Claim Gate Report         [planned]
P13 Metric Bridge Gate Hardening                  [planned]
```

Optional follow-up milestone:

```text
M2: Proxy-Regime and Paper Evidence Package
```

Recommended phase package:

```text
P14 Proxy-Regime Certification Matrix             [planned]
P15 Replay Evidence Package Builder               [planned]
P16 Paper Evidence Summary Builder                [planned]
```

Operator-facing milestone:

```text
M3: Scientific Closure and Runtime Adapter Preparation
```

Recommended phase package:

```text
P17 Phase 1 Scientific Closure Preparation         [planned / operator-required]
P18 Runtime Adapter Prototype v0                  [planned / dry-run first]
```

## 6. Branch strategy

Recommended after P10:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev

git switch codex/p10-provider-candidate-normalizer
git switch -c codex/milestone-runtime-audit-evidence-bridge
```

Then commit P11/P12/P13 on this milestone branch:

```text
codex/milestone-runtime-audit-evidence-bridge
  ├── P10 commit
  ├── P11 commit
  ├── P12 commit
  └── P13 commit
```

Original repo sync should wait until the milestone package is accepted.

## 7. Phase plan

### P11 — Provider-to-Selector Offline Smoke Path

Status:

```text
PLANNED / NEXT
```

Primary objective:

```text
Demonstrate that provider candidates can pass through the P10 normalizer and enter an offline selector/materializer-compatible path, producing ProjectionBundleV1 and complete conservative artifacts.
```

Proposed claim level:

```text
engineering_smoke_only
```

In scope:

- fake/local Graphiti-style candidates
- fake/local LangExtract-style candidates
- provider adapter output
- `normalize_candidate_pool(...)`
- selector/materializer-compatible candidate shape
- dry-run projection plan creation
- dry-run budget witness creation
- dry-run materialized context creation
- conservative metric bridge witness
- `ProjectionBundleV1` generation
- artifact completeness check
- deterministic summary output

Out of scope:

- live cohort
- live runtime integration
- SDK imports
- network calls
- real Graphiti / LangExtract execution
- measurement validation
- P04/P09 unblocking

Suggested implementation files:

```text
cps/experiments/provider_offline_smoke.py
tests/test_provider_offline_smoke.py
docs/experiments/provider-offline-smoke.md
```

Suggested artifact outputs:

```text
provider_candidates.jsonl
normalized_candidates.jsonl
projection_plans.jsonl
budget_witnesses.jsonl
materialized_contexts.jsonl
metric_bridge_witnesses.jsonl
projection_bundles.jsonl
summary.json
```

Acceptance criteria:

- provider-native candidates normalize successfully
- aliases exist after normalization
- input order is preserved
- fake Graphiti-style candidate path passes
- fake LangExtract-style candidate path passes
- ProjectionBundleV1 can embed normalized candidates
- artifact completeness passes only when required artifacts are present
- metric bridge claim remains conservative
- summary reports `engineering_smoke_only`
- deterministic rerun produces stable hashes / stable summary where applicable
- no network / SDK / reference access
- P04 and P09 remain blocked
- `measurement_validated` is not claimed

Suggested validation:

```powershell
python -m compileall cps scripts
pytest tests/test_provider_adapters.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_provider_offline_smoke.py -q
pytest tests/test_projection_bundle_v1.py -q
pytest tests/test_projection_artifacts.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Suggested commit message:

```text
Add provider-to-selector offline smoke path
```

---

### P12 — Evidence Ledger and Claim Gate Report

Status:

```text
PLANNED
```

Primary objective:

```text
Create a deterministic evidence ledger and claim gate report that summarize available artifacts, missing evidence, blocked phases, and the maximum allowed claim level.
```

Proposed claim level:

```text
replayable_artifact_evidence or lower, depending on evidence completeness
```

In scope:

- evidence ledger schema
- artifact count summary
- required artifact presence/absence
- projection bundle coverage
- stable hash coverage
- metric bridge status
- contamination status
- human labels status
- kappa status
- blocked phase status
- allowed claim level
- denied claim reasons
- JSON and Markdown reports

Out of scope:

- generating human labels
- computing real kappa from absent labels
- declaring measurement validation
- resolving P04/P09

Suggested implementation files:

```text
cps/experiments/evidence_ledger.py
cps/experiments/claim_gate_report.py
tests/test_evidence_ledger.py
tests/test_claim_gate_report.py
docs/experiments/evidence-ledger-and-claim-gate.md
```

Suggested outputs:

```text
evidence_ledger.json
claim_gate_report.json
claim_gate_report.md
```

Required reason codes:

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

Acceptance criteria:

- missing labels blocks `measurement_validated`
- missing kappa blocks `measurement_validated`
- contamination failure yields `pilot_only`
- missing/stale bridge yields `operational_utility_only` or `ambiguous`
- engineering-only evidence does not become scientific validation
- synthetic-only evidence does not certify deployment
- P04/P09 status appears in report
- report is deterministic
- Markdown report is human-readable
- no live execution or external dependency

Suggested validation:

```powershell
python -m compileall cps scripts
pytest tests/test_evidence_ledger.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
pytest tests/test_projection_artifacts.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Suggested commit message:

```text
Add evidence ledger and conservative claim gate report
```

---

### P13 — Metric Bridge Gate Hardening

Status:

```text
PLANNED
```

Primary objective:

```text
Harden the metric bridge gate so that bridge freshness, human labels, kappa, contamination, and evidence type determine the maximum allowed claim level through explicit fail-closed logic.
```

Proposed claim level:

```text
claim-gate hardening only; does not raise current project claim level
```

In scope:

- explicit metric bridge gate evaluator
- reason-coded fail-closed decisions
- test matrix for labels/kappa/contamination/freshness
- integration with evidence ledger or claim gate report
- docs explaining bridge gate boundaries

Out of scope:

- generating missing scientific evidence
- live Phase 1 closure
- runtime integration
- automatic upgrade to `measurement_validated`

Suggested implementation files:

```text
cps/runtime/claim_gate.py
# or cps/experiments/claim_gate.py if runtime/ is not appropriate

tests/test_metric_bridge_claim_gate.py
docs/architecture/metric-bridge-claim-gate.md
```

Suggested decision fields:

```text
metric_class
diagnostic_claim_level
bridge_freshness
human_labels_present
kappa_present
contamination_status
evidence_scope
measurement_validation_allowed
allowed_claim_level
reason_codes
```

Acceptance criteria:

- missing human labels => not `measurement_validated`
- missing kappa => not `measurement_validated`
- contamination failure => `pilot_only`
- stale bridge => `operational_utility_only` or `ambiguous`
- missing bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `synthetic_structural_only`
- engineering-only evidence => not scientific validation
- complete engineering artifacts alone do not imply `measurement_validated`
- tests cover fail-closed behavior
- P04/P09 remain unchanged

Suggested validation:

```powershell
python -m compileall cps scripts
pytest tests/test_metric_bridge_claim_gate.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Suggested commit message:

```text
Harden metric bridge claim gate
```

---

### P14 — Proxy-Regime Certification Matrix

Status:

```text
PLANNED
```

Primary objective:

```text
Convert synthetic regime results into an explicit proxy-regime certification matrix that documents expected behavior, observed diagnostic behavior, failure modes, and allowed claim levels.
```

Important boundary:

```text
Certification here means certification of the proxy diagnostic regime, not certification of deployed V-information submodularity.
```

Proposed claim level:

```text
synthetic_structural_only
```

Suggested implementation files:

```text
cps/experiments/proxy_regime_matrix.py
tests/test_proxy_regime_matrix.py
docs/experiments/proxy-regime-certification-matrix.md
```

Suggested outputs:

```text
proxy_regime_matrix.json
proxy_regime_matrix.md
```

Matrix fields:

```text
regime_name
structural_assumption
expected_selector_behavior
observed_diagnostic_behavior
failure_modes
allowed_claim_level
claim_denied_reasons
```

Acceptance criteria:

- redundancy regime summarized
- pairwise-synergy regime summarized
- higher-order / prerequisite regime summarized
- failure modes are explicit
- allowed claim remains `synthetic_structural_only`
- deployment certification is denied with reason codes
- output is deterministic

Suggested commit message:

```text
Add proxy-regime certification matrix
```

---

### P15 — Replay Evidence Package Builder

Status:

```text
PLANNED
```

Primary objective:

```text
Build deterministic replay packages that summarize artifact completeness, bundle hashes, claim gate results, and reproducibility metadata.
```

Proposed claim level:

```text
replayable_artifact_evidence
```

Suggested implementation files:

```text
cps/experiments/replay_package.py
tests/test_replay_package.py
docs/experiments/replay-package.md
```

Suggested CLI:

```powershell
python -m cps.experiments.replay_package --source <artifact_root> --output <package_root>
```

Suggested outputs:

```text
manifest.json
artifact_counts.json
bundle_hashes.json
claim_gate_report.json
summary.md
```

Acceptance criteria:

- deterministic package creation
- missing required artifacts fail closed
- missing projection bundles fail closed
- stable hash reporting
- claim gate result included
- no live artifacts generated
- no claim gate relaxation

Suggested commit message:

```text
Add deterministic replay evidence package builder
```

---

### P16 — Paper Evidence Summary Builder

Status:

```text
PLANNED
```

Primary objective:

```text
Generate manuscript-facing summaries of artifacts, claims, proxy regimes, replay evidence, limitations, and blocked scientific closure work.
```

Proposed claim level:

```text
manuscript_evidence_summary_only
```

Suggested implementation files:

```text
cps/experiments/paper_evidence_summary.py
tests/test_paper_evidence_summary.py
docs/experiments/paper-evidence-summary.md
```

Suggested outputs:

```text
paper_evidence_summary.json
paper_evidence_summary.md
```

Acceptance criteria:

- summarizes artifact schema
- summarizes claim ladder
- summarizes synthetic/proxy regime matrix
- summarizes replay evidence
- explicitly states limitations
- explicitly states missing labels/kappa block measurement validation
- explicitly states P04/P09 are blocked
- no scientific validation claim introduced

Suggested commit message:

```text
Add manuscript-facing paper evidence summary builder
```

---

### P17 — Phase 1 Scientific Closure Preparation

Status:

```text
PLANNED / OPERATOR_REQUIRED
```

Primary objective:

```text
Prepare the human/operator protocol required for scientific closure without running live Phase 1 or claiming measurement validation.
```

Proposed claim level:

```text
scientific_closure_protocol_prepared
```

In scope:

- label protocol
- annotator requirements
- kappa calculation plan
- contamination audit checklist
- metric bridge freshness criteria
- decision sheet template
- minimum evidence threshold
- failure handling

Out of scope:

- collecting labels
- computing kappa from real labels
- live cohort
- measurement validation

Suggested docs:

```text
docs/runbooks/phase1-scientific-closure-runbook.md
docs/runbooks/phase1-label-protocol.md
docs/runbooks/phase1-contamination-audit.md
```

Acceptance criteria:

- operator checklist complete
- label/kappa/contamination/freshness requirements explicit
- failure handling explicit
- still blocked until operator execution

Suggested commit message:

```text
Prepare Phase 1 scientific closure protocol
```

---

### P18 — Runtime Adapter Prototype v0

Status:

```text
PLANNED / DRY-RUN FIRST / OPERATOR_REQUIRED FOR LIVE
```

Primary objective:

```text
Define and test a dry-run runtime adapter contract without live external integration.
```

Proposed claim level:

```text
runtime_adapter_contract_dry_run_only
```

Suggested contract types:

```text
RuntimeEvent
ProjectionRequest
ProjectionResponse
ProjectionBundleExport
```

Out of scope:

- production runtime integration
- network calls
- external SDK imports
- live execution
- P09 unblocking without operator approval

Acceptance criteria:

- local/fake adapter contract works
- ProjectionBundle export path remains deterministic
- no live runtime calls
- P09 remains blocked unless explicitly changed by operator-reviewed phase

Suggested commit message:

```text
Add dry-run runtime adapter contract prototype
```

## 8. Milestone acceptance criteria

M1 can be accepted when:

- P10 is accepted
- P11 offline smoke path passes
- P12 claim gate report exists
- P13 metric bridge gate tests pass
- framework guard passes
- docs clearly state claim boundaries
- P04 remains blocked/operator-required
- P09 remains blocked/operator-required
- `measurement_validated` is not claimed
- no live APIs or external runtime integration were used
- original repo sync plan is explicit but not automatically executed unless requested

M1 allowed summary:

```text
M1 ACCEPT: provider-compatible CPS runtime-audit evidence bridge implemented with deterministic offline smoke evidence and conservative claim gating.
```

M1 forbidden summary:

```text
CPS scientifically validated.
Deployed V-information submodularity certified.
Runtime integration complete.
Measurement validated.
P04/P09 unblocked.
```

## 9. Sync strategy after milestone acceptance

Only after milestone acceptance, sync from `mingx-dev` to `mingx`:

```powershell
cd C:\Users\Mingx\Documents\mx-codex\mingx

git status --short
git switch main
git pull --ff-only origin main
git switch -c codex/sync-runtime-audit-evidence-bridge

git fetch "C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev" codex/milestone-runtime-audit-evidence-bridge:refs/remotes/mingx-dev/runtime-audit-evidence-bridge
```

Then either cherry-pick the accepted commits or merge the fetched milestone branch, depending on the desired history policy.

Required validation after sync:

```powershell
python -m compileall cps scripts
pytest tests/test_provider_adapters.py -q
pytest tests/test_provider_candidate_normalizer.py -q
pytest tests/test_projection_bundle_v1.py -q
pytest tests/test_selector_optional_adapters.py -q
pytest tests/test_synthetic_regime_benchmark.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Add phase-specific tests as they are created.

## 10. Development prompt invariant

Every future Codex prompt for this milestone should include:

```text
Work only in mingx-dev.
Do not sync to mingx unless explicitly requested.
Do not push GitHub PR unless explicitly requested.
Do not modify reference/.
Do not run live APIs.
Do not run live cohort.
Do not unblock P04/P09.
Do not claim measurement_validated.
Do not report engineering success as scientific validation.
Do not infer deployed V-information submodularity from synthetic success.
```
