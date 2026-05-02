# Engineering Debt and Paper-Relevance Audit

```yaml
phase_id: P19
phase_title: Engineering Debt and Paper-Relevance Audit
verdict: ACCEPT
document_type: audit_only
branch: codex/p19-engineering-debt-paper-relevance-audit
measurement_validated_claimed: false
p04_status: BLOCKED_OPERATOR_REQUIRED
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_required: false
external_runtime_required: false
dependency_changes: none
```

## 1. Audit Objective

P19 is a documentation-only audit. Its goal is to keep the repository aligned with the paper:

> Context Projection Selection in Multi-Agent Systems: Conditional Theory, Metric Bridge, and Proxy-Regime Certification

The project boundary is narrow: CPS measurement and runtime-audit evidence, not a general agent framework. The audit identifies which modules remain core to the evidence chain, which modules should be frozen, which documents should be appendix-only, and which future work requires operator approval. The goal is to prevent code-heavy scaffold growth that does not strengthen the manuscript, claim gate, replay evidence, metric bridge, proxy-regime evidence, or P04 scientific closure readiness.

## 2. Current Evidence Chain Summary

The accepted P10-P18 chain is:

| Phase | Evidence role | Claim boundary |
| --- | --- | --- |
| P10 Provider candidate normalization | Bridges provider payload aliases into selector/materializer-compatible candidate items. | Engineering compatibility only. |
| P11 Provider-to-selector offline smoke path | Creates deterministic fake/local provider-to-selector artifacts and `ProjectionBundleV1` bundles. | Offline engineering smoke only. |
| P12 Evidence ledger and claim gate report | Summarizes available evidence and denies unsupported claims conservatively. | Audit/reporting only. |
| P13 Metric bridge gate hardening | Makes bridge freshness, labels, kappa, contamination, and evidence mode visible in claim gates. | Claim-gate tightening only. |
| P14 Proxy-regime certification matrix | Converts synthetic/proxy regimes into manuscript-facing diagnostic matrix rows. | Proxy/synthetic diagnostic only. |
| P15 Replay evidence package | Packages artifacts, hashes, ledger, claim report, and optional matrix into stable evidence outputs. | Replay packaging only. |
| P16 Paper evidence summary | Converts replay evidence into manuscript-facing JSON/Markdown summaries and table rows. | Paper summary only; no claim upgrade. |
| P17 End-to-end evidence demo | Wires P10-P16 into one deterministic offline evidence chain. | Offline runtime-audit demo only. |
| P18 Manuscript integration patch | Produces tables and patch text for `docs/archive/context_projection_revised_v10.md`. | Manuscript integration only. |

The chain supports end-to-end evidence demo, manuscript tables, conservative claim gate hardening, replay reproducibility, metric bridge/proxy-regime evidence, and readiness for future human-label/kappa/contamination work. It does not execute P04 or P09.

## 3. Classification Legend

| Classification | Meaning | Default policy |
| --- | --- | --- |
| `KEEP_CORE` | Directly used by P17, P18, claim gate, or replay evidence. | Keep in core; only bug fixes, determinism fixes, claim-gate tightening, or manuscript integration fixes. |
| `KEEP_FROZEN` | Useful support code, but not the central evidence chain. | Freeze feature expansion unless needed by P17/P18 or operator-approved P04/P09 work. |
| `APPENDIX_ONLY` | Useful review, roadmap, runbook, or design reference. | Keep as supporting documentation, not a core claim-bearing artifact. |
| `FUTURE_REMOVAL_CANDIDATE` | Unused, duplicated, disconnected from claim gate/replay/manuscript. | Do not expand; remove later if no paper/evidence role emerges. |
| `OPERATOR_REQUIRED_FUTURE_WORK` | Requires P04/P09 operator approval, live cohort, runtime integration, labels, kappa, contamination, or metric bridge closure. | Keep blocked until explicit operator approval. |

## 4. Module Classification Matrix

| path | classification | role | paper relevance | used by P17 demo? | used by P18 manuscript patch? | supports claim gate? | supports replay? | bloat risk | recommended action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cps/schema/projection_bundle_v1.py` | `KEEP_CORE` | Canonical projection bundle schema and stable hash. | Central runtime-audit evidence object. | yes | yes | yes | yes | low | Freeze except schema bug fixes and deterministic serialization fixes. |
| `cps/providers/normalizer.py` | `KEEP_CORE` | Provider candidate alias bridge for selector/materializer compatibility. | Enables P10-P17 evidence chain from provider-like records. | yes | indirectly | no | yes | low | Keep minimal; no new provider semantics. |
| `cps/experiments/provider_offline_smoke.py` | `KEEP_CORE` | Deterministic fake provider-to-selector smoke path. | Demonstrates offline evidence chain inputs. | yes | indirectly | yes | yes | medium | Keep as paper evidence smoke path; no live provider expansion. |
| `cps/experiments/evidence_ledger.py` | `KEEP_CORE` | Deterministic evidence summary from artifacts or in-memory summaries. | Provides audit ledger for claim boundary. | yes | indirectly | yes | yes | low | Freeze except required artifact or determinism fixes. |
| `cps/experiments/claim_gate_report.py` | `KEEP_CORE` | Conservative claim gate report. | Primary paper claim-boundary surface. | yes | yes | yes | yes | low | Keep as the single top-level claim report; do not duplicate. |
| `cps/experiments/metric_bridge_gate.py` | `KEEP_CORE` | Bridge-specific gate for freshness, labels, kappa, contamination, and evidence mode. | Supports Metric Bridge section and denied claims. | yes | yes | yes | yes | low | Keep integrated with P12 report; tighten only. |
| `cps/experiments/proxy_regime_matrix.py` | `KEEP_CORE` | Synthetic/proxy regime diagnostic matrix. | Supports Proxy-Regime Certification section. | yes | yes | yes | yes | low | Keep as matrix source of truth; no deployed certification claims. |
| `cps/experiments/replay_evidence_package.py` | `KEEP_CORE` | Stable replay evidence package builder. | Supports replayable experiment evidence section. | yes | yes | yes | yes | low | Freeze output contract except manuscript/replay bug fixes. |
| `cps/experiments/paper_evidence_summary.py` | `KEEP_CORE` | Manuscript-facing summary over replay package outputs. | Supports paper tables and limitations. | yes | yes | yes | yes | low | Keep as P16 paper evidence source; no claim upgrades. |
| `cps/experiments/end_to_end_evidence_demo.py` | `KEEP_CORE` | Offline P10-P16 demo pipeline. | Proves complete offline runtime-audit evidence chain. | yes | yes | yes | yes | low | Keep deterministic and offline-only. |
| `cps/experiments/manuscript_tables.py` | `KEEP_CORE` | P18 manuscript table and patch builder. | Directly targets `context_projection_revised_v10.md`. | no | yes | yes | yes | low | Keep as manuscript integration tool; no runtime behavior. |
| `cps/experiments/artifacts.py` | `KEEP_FROZEN` | Projection event/artifact summary helpers. | Supports artifact completeness and bundle counts. | indirectly | indirectly | yes | yes | low | Freeze except completeness or determinism fixes. |
| `cps/experiments/synthetic_benchmark.py`, `synthetic_regimes.py`, `selection.py`, `reporting.py` | `KEEP_FROZEN` | Synthetic structural benchmark and reporting. | Supports P05 and P14 proxy-regime evidence. | indirectly | indirectly | yes | yes | medium | Keep as structural benchmark only; do not treat as deployed certification. |
| `cps/experiments/phase_b_replay.py`, `decision.py`, `diagnostics.py` | `KEEP_FROZEN` | Earlier replay/diagnostic support. | Useful background for replay and diagnostics. | no | no | partial | partial | medium | Keep frozen; expand only if P17/P18 or P04 requires it. |
| `cps/providers/graphiti_provider.py`, `langextract_provider.py`, `common.py` | `KEEP_FROZEN` | Dependency-free fake/local provider conversion adapters. | Supports P08/P11 inputs. | indirectly | no | no | partial | medium | Freeze; no new provider families unless directly used by evidence demo or operator-approved runtime work. |
| `cps/providers/openai_compatible.py`, `dashscope.py` | `OPERATOR_REQUIRED_FUTURE_WORK` | Live chat backend providers. | Outside current offline evidence chain. | no | no | no | no | high | Do not expand or run without explicit operator approval. |
| `cps/selectors/common.py`, `submodlib_selector.py`, `ortools_oracle.py` | `KEEP_FROZEN` | Optional selector/oracle adapters. | Appendix support for benchmark comparisons. | no | no | partial | no | medium | Keep optional/dependency-guarded; no new selector framework work. |
| `cps/export/common.py`, `otel.py`, `langfuse.py`, `phoenix.py` | `KEEP_FROZEN` | Dry-run observability exporter payloads. | Appendix observability mappings. | no | no | no | partial | medium | Keep frozen unless replay package or paper tables consume outputs. |
| `docs/archive/context_projection_revised_v10.md` | `KEEP_CORE` | Source manuscript. | Primary paper artifact. | no | yes | yes | yes | low | Do not rewrite in P19; P20 decides integration strategy. |
| `docs/paper/context_projection_v10_p18_tables_and_experiment_patch.md` | `KEEP_CORE` | P18 manuscript integration patch. | Direct manuscript patch source. | no | yes | yes | yes | low | Keep as companion patch until P20 decides merge/appendix/restructure. |
| `docs/reviews/milestone-runtime-audit-evidence-bridge-review.md`, `milestone-proxy-regime-replay-paper-evidence-review.md`, `P10-P18 reviews` | `APPENDIX_ONLY` | Audit trail and milestone acceptance evidence. | Supports review traceability. | no | indirect | yes | yes | low | Keep as appendix/review trail; do not treat as scientific evidence. |
| `docs/roadmaps/`, `docs/runbooks/`, `docs/architecture/`, `docs/protocols/`, `docs/reference-projects-local.md` | `APPENDIX_ONLY` | Planning, operator runbooks, architecture notes, reference index. | Supports project governance and future work. | no | indirect | partial | partial | medium | Keep as appendix docs; do not expand without paper relevance. |
| `.state/codex/current_phase.json`, `.state/codex/phase_history.jsonl`, P04/P09 state | `OPERATOR_REQUIRED_FUTURE_WORK` | Framework phase state and blocked operator phases. | Preserves claim-gate status. | no | yes | yes | no | low | Keep P04/P09 blocked until explicit operator action. |
| P04 labels, kappa, contamination, bridge closure artifacts | `OPERATOR_REQUIRED_FUTURE_WORK` | Missing scientific closure evidence. | Required for any validation-level future claim. | no | yes | yes | yes | low | Do not synthesize; must be operator/human-reviewed. |
| External runtime adapter implementation after P09 | `OPERATOR_REQUIRED_FUTURE_WORK` | Future runtime integration. | Could support operational evidence only after approval. | no | no | no | no | high | Do not start without operator approval. |
| Any future unused provider/exporter/adapter/report generator | `FUTURE_REMOVAL_CANDIDATE` | Unused scaffold. | None unless tied to P17/P18/P04/P09. | no | no | no | no | high | Reject by default; remove if it does not support paper evidence. |

## 5. Bloat-Risk Findings

1. **Unused adapters can become generic framework work.** Provider and selector adapters are useful only when they feed P17/P18 evidence, P04 scientific closure, or P09 operator-approved runtime work. New adapters should be rejected unless they have a direct evidence-chain use.
2. **Exporters are appendix/frozen unless used by evidence packages.** Dry-run OTel/Langfuse/Phoenix exporters are observability mappings, not paper evidence by themselves. They should remain frozen until replay packages or manuscript tables consume them.
3. **Duplicate claim-gate logic must not be introduced.** P12/P13 are the claim gate source of truth. P14-P18 should consume those outputs and must not create a competing validation policy.
4. **Report generators not used by P17/P18 should be frozen or removed later.** A report generator is core only if it feeds the end-to-end demo, replay package, paper evidence summary, or manuscript patch.
5. **Mock/fake paths must support paper evidence or remain test-only.** Fake Graphiti/LangExtract paths are acceptable because P11/P17 use them for deterministic smoke evidence; additional fake paths need the same justification.
6. **Generic agent framework modules are out of scope.** Scheduling, tool execution, memory lifecycle, live providers, and external runtime orchestration remain outside the CPS measurement scaffold unless P09 operator approval changes scope.

## 6. Freeze Policy

P10-P18 modules are frozen except for:

- bug fixes,
- claim-gate tightening,
- determinism fixes,
- artifact completeness fixes,
- manuscript integration fixes,
- P04 operator-approved scientific closure work,
- P09 operator-approved runtime integration work.

Do not add new providers, exporters, adapters, selectors, report generators, or scaffold layers unless they directly support:

- P17 end-to-end evidence demo,
- P18/P20 manuscript integration,
- P04 labels/kappa/contamination/metric bridge closure,
- P09 operator-approved runtime adapter work.

No new scaffold should be accepted without direct manuscript table or replay evidence package use.

## 7. Deletion / Appendix Policy

- **Keep in core** if the module is used by the evidence demo, manuscript patch, claim gate, replay package, metric bridge gate, or proxy-regime matrix.
- **Move to appendix** if the item is useful as design reference, roadmap, review trace, or runbook but is not part of the claim-bearing evidence chain.
- **Mark for future removal** if it is unused, duplicated, disconnected from claim gates/replay/manuscript, or only supports generic agent-framework expansion.
- **Keep blocked** if it requires P04 or P09 operator work: live cohort, external runtime integration, human labels, kappa, contamination closure, or fresh metric bridge evidence.

## 8. Claim Boundary

- P19 is an audit only.
- P19 is not scientific validation.
- `measurement_validated` is not claimed.
- Engineering completeness is not scientific validation.
- Synthetic success is not deployed V-information certification.
- Replay package completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.

## 9. Next Recommended Step

Next recommended step: **P20 Context Projection v10 Manuscript Integration Decision**.

P20 should decide whether to:

1. partially merge the P18 patch into `docs/archive/context_projection_revised_v10.md`,
2. keep the P18 patch as a companion evidence appendix,
3. revise the manuscript structure before integration.

P20 should remain manuscript-integration planning/review unless explicitly approved to edit the source manuscript.
