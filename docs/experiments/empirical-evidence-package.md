# Empirical Evidence Package

**Phase:** P28 Contamination and Live Evidence Package Integration

**Status:** Empirical evidence packaging and gating layer. P28 does not execute
live APIs, collect labels, compute new kappa from fabricated labels, or complete
empirical validation.

## 1. Purpose

P28 integrates future empirical evidence artifacts into one deterministic
package:

```text
controlled live pilot summary
  -> human label completeness report
  -> kappa report
  -> contamination report
  -> metric bridge freshness status
  -> empirical claim gate summary
  -> empirical evidence package
```

The package extends the CPS runtime-audit evidence stack. It does not replace
the existing conservative claim gate.

## 2. Inputs

The builder consumes either an in-memory mapping or a P26-style output directory.

Supported inputs include:

- `run_manifest.json`
- `pilot_summary.json`
- `claim_gate_report.json`
- `evidence_ledger.json`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- metric bridge freshness status
- artifact completeness status

Missing label, kappa, contamination, or bridge artifacts fail closed. They do
not become validation evidence.

## 3. Outputs

The package can write:

- `empirical_evidence_manifest.json`
- `live_pilot_summary.json`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`

The manifest records:

- controlled live run presence;
- live API usage;
- human-label completeness;
- kappa status;
- contamination status;
- metric bridge freshness;
- artifact completeness;
- allowed empirical claim level;
- denied claims;
- stable reason codes;
- P04/P09 status.

## 4. Claim Mapping

| Evidence state | Allowed empirical claim level |
| --- | --- |
| No controlled live run | `not_empirical_validation` |
| Live run without labels | `controlled_live_pilot_only` |
| Missing labels | Not `measurement_validated` |
| Missing kappa | Not `measurement_validated` |
| Low kappa | `pilot_only` or weak evidence |
| Contamination failed | `pilot_only` |
| Contamination unknown/incomplete | Not `measurement_validated` |
| Stale bridge | `operational_utility_only` |
| Missing bridge | `ambiguous` |
| High kappa, contamination pass, fresh bridge, complete artifacts | At most `measurement_validated_candidate` unless the existing claim gate explicitly allows more. |

Even favorable evidence remains a candidate until all external requirements and
the existing claim gate allow a stronger claim.

## 5. Relationship To P26 And P27

P26 provides controlled live pilot scaffolding and case artifacts. P27 provides
human-label completeness and kappa reports. P28 packages those reports with
contamination and metric bridge evidence.

P28 does not:

- run the P26 live mode;
- call a model API;
- fabricate labels;
- fabricate kappa;
- fabricate contamination clearance;
- unblock P04 or P09.

## 6. Claim Boundary

- P28 does not complete empirical validation.
- Live API success alone is not measurement validation.
- Human labels and acceptable kappa are required.
- High kappa alone is not measurement validation.
- Contamination pass alone is not measurement validation.
- Fresh metric bridge evidence is required.
- Existing claim gate approval is required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed by default.
