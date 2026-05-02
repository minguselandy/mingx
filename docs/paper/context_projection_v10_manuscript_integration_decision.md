# Context Projection v10 Manuscript Integration Decision

## 1. Target Manuscript

Target manuscript:

```text
docs/archive/context_projection_revised_v10.md
```

P20 is a manuscript-integration decision phase only. It does not modify the target manuscript. P21 should apply only the approved subset of edits directly to the source manuscript.

## 2. Decision Summary

Recommended strategy: `INTEGRATE_CORE_TABLES_ONLY`.

Rationale:

- The current manuscript already contains substantial conservative framing for conditional theory, metric bridge scope, proxy-regime labeling, runtime-audit requirements, and limitations.
- Full P18 insertion would duplicate Section 3.4, Section 4.3.1, Section 6, and Section 9.
- The main body should gain only compact evidence and claim-boundary material that improves manuscript clarity.
- Detailed P18 tables should remain in the companion patch or appendix unless a later restructuring phase approves full appendix integration.

Rejected strategies:

| strategy | decision | reason |
| --- | --- | --- |
| `INTEGRATE_EXPERIMENT_SECTION_PATCH` | rejected as primary | Too narrow; P21 needs small additions in runtime-audit and limitations sections as well. |
| `KEEP_PATCH_AS_COMPANION_APPENDIX` | rejected as primary | Too weak; the main manuscript should include a compact runtime-audit evidence bridge. |
| `RESTRUCTURE_BEFORE_INTEGRATION` | rejected for P20 | Manuscript structure is already coherent enough for targeted edits. |
| `DEFER_UNTIL_LIVE_OR_LABEL_EVIDENCE` | rejected for P20 | The offline audit scaffold is paper-relevant as engineering evidence, provided claims stay bounded. |

## 3. Section-by-Section Integration Plan

| manuscript section | modify in P21? | P18 material to insert | placement | claim boundary impact | duplication risk |
| --- | --- | --- | --- | --- | --- |
| Abstract / Introduction | optional, one sentence only | State that runtime-audit evidence is replayable/offline evidence only. | Body, one sentence if needed. | Must not imply scientific validation. | Low if limited to one sentence. |
| Problem formulation | no | None. Current per-round candidate pool framing is aligned. | None. | No change. | Low. |
| Conditional theory | no | None. Keep engineering artifacts separate from theorem claims. | None. | Preserves theorem/proxy separation. | Low. |
| Metric bridge | yes | Condensed conservative claim-gate paragraph and compact Table 2. | Body after Section 3.4 bridge table or near Section 4.2. | Strengthens denial of unsupported claims. | Medium; avoid repeating existing bridge regimes. |
| Runtime-audit scaffold | yes | Compact Table 1 focused on core artifacts and P10-P18 evidence outputs. | Body near Section 6.2 four-artifact projection chain. | Shows audit surface without validation claims. | Medium; Section 6.2 already describes core artifacts. |
| Proxy-regime certification | limited | Short cross-reference to companion P18 matrix only. | Body footnote/short paragraph after Section 4.3.1 if needed. | Maintains proxy-only scope. | High if full Table 3 is inserted. |
| Experiments / evidence | yes | Short offline P17 evidence-chain paragraph. | Body after Section 4.3.1 validity gate. | Explicitly denies scientific validation. | Low if one paragraph. |
| Limitations | yes | Compact non-claims paragraph or small table based on Table 5. | Body in Section 9. | Reinforces P04/P09 and validation boundaries. | Low; complements existing limitations. |
| Appendix / artifacts | defer | Full Table 3 and Table 4, plus detailed P18 companion patch. | Companion doc or future appendix. | Keeps details inspectable but outside main claims. | Low if kept companion-only. |

## 4. Table Integration Plan

| P18 table | main body? | appendix? | companion only? | target section | reason | claim-boundary warning |
| --- | --- | --- | --- | --- | --- | --- |
| Table 1: CPS Runtime-Audit Artifacts | yes, compact | no for P21 | no | Section 6.2 | Directly supports runtime-audit scaffold and P17 evidence chain. | Audit interface only; not scientific validation. |
| Table 2: Conservative Claim Gate Rules | yes, compact | no for P21 | no | Section 3.4 or 4.2 | Clarifies metric bridge and claim-gate semantics. | Does not claim `measurement_validated`. |
| Table 3: Proxy-Regime Certification Matrix | no | possible future appendix | yes for P21 | Companion P18 patch | Full matrix duplicates Section 4.3.1. | Proxy-regime certification is not deployed V-information certification. |
| Table 4: Replay Evidence Package Summary | no | possible future appendix | yes for P21 | Companion P18 patch | Too implementation-specific for main body. | Replay package completeness is not scientific validation. |
| Table 5: Limitations and Non-Claims | yes, compact paragraph or small table | no for P21 | no | Section 9 | Reinforces existing limitations and P04/P09 boundaries. | Paper-facing summaries do not upgrade claim levels. |

## 5. Claim Downgrade Checklist

The manuscript is already conservative overall. P21 should use local guardrails for the following terms rather than deleting the paper's terminology wholesale.

| phrase or nearby context | why risky | recommended replacement or guardrail | apply in P21? |
| --- | --- | --- | --- |
| `certified proxy-greedy-valid` | Could be read as deployed V-information certification without the metric bridge qualifier. | `certified proxy-greedy-valid under a fresh metric bridge and fixed calibration conditions` | yes |
| `certified greedy-valid` | Could be read as unconditional selector correctness. | `proxy-greedy-valid under the active metric-claim regime` | yes |
| `certified escalate` | Could imply escalation is scientifically validated. | `diagnostics-supported escalation label under sufficient bridge and sample evidence` | yes |
| `Vinfo_proxy_certified` | Could be confused with deployed V-information certification. | `Vinfo_proxy_certified only under validated metric bridge conditions` | yes |
| `proxy-regime certification` | Title-level term is acceptable but needs recurring scope boundary. | `proxy-regime certification, not deployed V-information certification` | yes |
| `composite certification` | Could imply full system certification. | `composite proxy-regime certification with explicit failure events` | yes |
| `guarantee` near runtime/pipeline discussion | Formal guarantees do not transfer to heuristic runtime behavior. | Use `formal guarantee` only for Section 3 theorem statements; use `audit signal` for runtime. | yes |
| `validated utility-to-log-loss bridge` | Acceptable if tied to explicit calibration evidence. | Keep, but require freshness, active stratum, labels/kappa where relevant. | yes |

No direct `measurement_validated`, `scientifically validated`, `deployed V-information certified`, `live validation`, `production integration`, or `human-validated` claim was found in the inspected manuscript text. P21 should preserve that absence.

## 6. Required Non-Claims

P20 preserves the following boundaries:

- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.
- Synthetic benchmark success does not certify deployed V-information submodularity.
- Proxy-regime certification is not deployed V-information certification.
- Replay package completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.
- Live API success alone is not measurement validation.
- External runtime success alone is not measurement validation.

## 7. P21 Editing Instructions

P21 should apply only compact, approved edits directly to:

```text
docs/archive/context_projection_revised_v10.md
```

P21 should not paste the entire P18 companion patch into the manuscript. It should integrate:

1. a compact runtime-audit artifact table in Section 6.2,
2. a compact conservative claim-gate table or paragraph near Section 3.4 or 4.2,
3. a short offline evidence-chain paragraph after Section 4.3.1,
4. a compact non-claims paragraph in Section 9,
5. local guardrails for risky certification terms.

## 8. Recommended Next Step

Next recommended phase: **P21 Context Projection v10 Manuscript Integration Patch Application**.

P21 should apply the approved subset of P18/P20 edits directly to `docs/archive/context_projection_revised_v10.md` while preserving the hard claim boundaries above.
