from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.claim_gate_report import build_claim_gate_report
from cps.experiments.decision import is_synthetic_diagnostic_scope
from cps.experiments.decision import normalize_diagnostic_scope
from cps.experiments.decision import normalize_metric_claim_level
from cps.experiments.evidence_ledger import (
    build_evidence_ledger_from_artifact_dir,
    build_evidence_ledger_from_summary,
)


MATRIX_VERSION = "ProxyRegimeDiagnosisMatrixV1"
PROXY_REGIME_ENTRY_ORDER = (
    "redundancy_dominated",
    "sparse_pairwise_synergy",
    "higher_order_synergy",
    "contamination_failed",
    "missing_human_labels",
    "missing_kappa",
    "stale_metric_bridge",
    "missing_metric_bridge",
    "artifact_incomplete",
)
DIAGNOSTIC_SCOPES = (
    "proxy_regime_diagnostic_only",
    "synthetic_structural_only",
    "oracle_structural_only",
    "synthetic_oracle_structural_only",
    "engineering_smoke_only",
    "ambiguous_metric",
    "pilot_only",
)
CERTIFICATION_SCOPES = DIAGNOSTIC_SCOPES
DENIED_SCOPE_VALUES = (
    "deployed_V_information_certified",
    "measurement_validated",
    "scientific_validation",
)
CLAIM_BOUNDARY_WARNING = (
    "proxy-regime diagnosis is not deployed V-information certification; "
    "measurement_validated is not claimed; "
    "P04 remains BLOCKED_OPERATOR_REQUIRED; "
    "P09 remains BLOCKED_OPERATOR_REQUIRED"
)

REGIME_DEFINITIONS: dict[str, dict[str, str]] = {
    "redundancy_dominated": {
        "structural_assumption": "Clustered near-duplicate candidates with strong diminishing residual value.",
        "expected_selector_behavior": "monitored_greedy",
        "expected_diagnostic_behavior": "High block-ratio proxy, low synergy mass, and small greedy-vs-augmented gap.",
    },
    "sparse_pairwise_synergy": {
        "structural_assumption": "Sparse bounded pairwise complementarities among otherwise useful candidates.",
        "expected_selector_behavior": "seeded_augmented_greedy",
        "expected_diagnostic_behavior": "Detected pairwise interaction mass and escalation away from plain greedy.",
    },
    "higher_order_synergy": {
        "structural_assumption": "Higher-order prerequisite or triple interactions where pairwise diagnostics are insufficient.",
        "expected_selector_behavior": "interaction_aware_local_search",
        "expected_diagnostic_behavior": "Triple-excess or higher-order ambiguity diagnostic fires and greedy support is withheld.",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stable_write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _bridge_overrides_from_witnesses(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    witness_rows = [dict(row) for row in rows]
    if not witness_rows:
        return {
            "metric_bridge_witness_count": 0,
            "bridge_freshness": "missing",
            "metric_class": "missing",
            "diagnostic_claim_level": "ambiguous_metric",
        }
    drift_statuses = {str(row.get("drift_status", "missing")) for row in witness_rows}
    if "stale" in drift_statuses:
        bridge_freshness = "stale"
    elif drift_statuses == {"fresh"}:
        bridge_freshness = "fresh"
    else:
        bridge_freshness = "missing"
    metric_classes = sorted({str(row.get("metric_class", "unknown")) for row in witness_rows})
    diagnostic_claim_levels = sorted({str(row.get("diagnostic_claim_level", "ambiguous_metric")) for row in witness_rows})
    return {
        "metric_bridge_witness_count": len(witness_rows),
        "bridge_freshness": bridge_freshness,
        "metric_class": metric_classes[0] if len(metric_classes) == 1 else "mixed",
        "diagnostic_claim_level": diagnostic_claim_levels[0] if len(diagnostic_claim_levels) == 1 else "mixed",
    }


def _matrix_evidence_overrides(explicit_overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    explicit = deepcopy(dict(explicit_overrides or {}))
    if any(key in explicit for key in ("evidence_mode", "evidence_scope", "diagnostic_scope")):
        return explicit
    return {
        "evidence_mode": "synthetic_structural_only",
        "evidence_scope": "synthetic_structural_only",
        **explicit,
    }


def _rows_by_regime(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        payload = dict(row)
        grouped.setdefault(str(payload.get("regime", "unknown")), []).append(payload)
    return {key: grouped[key] for key in sorted(grouped)}


def _observed_behavior(regime: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing diagnostics"
    selector_actions = sorted({str(row.get("selector_action", "unknown")) for row in rows})
    selector_labels = sorted({str(row.get("selector_regime_label", "unknown")) for row in rows})
    synergy_values = [row.get("synergy_fraction") for row in rows if row.get("synergy_fraction") is not None]
    pairwise_values = [row.get("pairwise_synergy_mass") for row in rows if row.get("pairwise_synergy_mass") is not None]
    triple_flags = sorted({str(row.get("triple_excess_flag", "unknown")) for row in rows})
    parts = [
        f"dispatches={len(rows)}",
        f"selector_actions={','.join(selector_actions)}",
        f"selector_labels={','.join(selector_labels)}",
    ]
    if synergy_values:
        avg_synergy = sum(float(value) for value in synergy_values) / len(synergy_values)
        parts.append(f"avg_synergy_fraction={avg_synergy:.6f}")
    if pairwise_values:
        avg_pairwise = sum(float(value) for value in pairwise_values) / len(pairwise_values)
        parts.append(f"avg_pairwise_synergy_mass={avg_pairwise:.6f}")
    if regime == "higher_order_synergy":
        parts.append(f"triple_flags={','.join(triple_flags)}")
    return "; ".join(parts)


def _artifact_status(ledger: Mapping[str, Any]) -> str:
    return "complete" if bool(ledger.get("required_artifacts_present")) else "incomplete"


def _diagnostic_scope(
    *,
    regime_name: str,
    allowed_claim_level: str,
    evidence_scope: str,
    required_artifacts_present: bool,
) -> str:
    normalized_claim_level = normalize_metric_claim_level(allowed_claim_level)
    normalized_evidence_scope = normalize_diagnostic_scope(evidence_scope)
    if allowed_claim_level == "pilot_only":
        return "pilot_only"
    if not required_artifacts_present or normalized_claim_level == "ambiguous_metric":
        if regime_name in REGIME_DEFINITIONS and is_synthetic_diagnostic_scope(normalized_evidence_scope):
            return normalized_evidence_scope
        return "ambiguous_metric"
    if allowed_claim_level == "engineering_smoke_only":
        return "engineering_smoke_only"
    if regime_name in REGIME_DEFINITIONS:
        return "proxy_regime_diagnostic_only"
    return "ambiguous_metric"


def _effective_allowed_claim_level(report: Mapping[str, Any]) -> str:
    allowed_claim_level = normalize_metric_claim_level(report["allowed_claim_level"])
    allowed_bridge_claim_level = normalize_metric_claim_level(report.get("allowed_bridge_claim_level", allowed_claim_level))
    if allowed_claim_level == "pilot_only" or allowed_bridge_claim_level == "pilot_only":
        return "pilot_only"
    if allowed_claim_level == "ambiguous_metric" or allowed_bridge_claim_level == "ambiguous_metric":
        return "ambiguous_metric"
    if allowed_bridge_claim_level == "operational_utility_only":
        return "operational_utility_only"
    return allowed_claim_level


def _failure_modes(
    *,
    diagnostics_rows: list[dict[str, Any]],
    report: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> list[str]:
    failures: set[str] = set()
    if not diagnostics_rows:
        failures.add("missing_diagnostics")
    if not bool(ledger.get("required_artifacts_present")):
        failures.add("artifact_incomplete")
    if int(ledger.get("projection_bundle_count", 0) or 0) <= 0:
        failures.add("missing_projection_bundles")
    for reason in report.get("reason_codes", []):
        if reason in {
            "contamination_failed",
            "missing_human_labels",
            "missing_kappa",
            "missing_metric_bridge",
            "stale_metric_bridge",
            "engineering_evidence_only",
            "synthetic_only_not_deployed_certification",
        }:
            failures.add(str(reason))
    failures.add("deployed_v_information_certification_denied")
    return sorted(failures)


def _entry_from_report(
    *,
    regime_name: str,
    evidence_mode: str,
    structural_assumption: str,
    expected_selector_behavior: str,
    expected_diagnostic_behavior: str,
    observed_diagnostic_behavior: str,
    ledger: Mapping[str, Any],
    report: Mapping[str, Any],
    diagnostics_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    required_artifacts_present = bool(ledger.get("required_artifacts_present"))
    allowed_claim_level = _effective_allowed_claim_level(report)
    return {
        "regime_name": regime_name,
        "evidence_mode": evidence_mode,
        "structural_assumption": structural_assumption,
        "expected_selector_behavior": expected_selector_behavior,
        "expected_diagnostic_behavior": expected_diagnostic_behavior,
        "observed_diagnostic_behavior": observed_diagnostic_behavior,
        "artifact_completeness_status": _artifact_status(ledger),
        "metric_bridge_status": str(report.get("metric_bridge_gate_status", "unknown")),
        "claim_gate_status": "measurement_denied"
        if not bool(report.get("measurement_validated_allowed"))
        else "measurement_review_eligible",
        "allowed_claim_level": allowed_claim_level,
        "denied_claims": list(report.get("denied_claims", [])),
        "reason_codes": list(report.get("reason_codes", [])),
        "reason_code_order": list(report.get("reason_code_order", [])),
        "failure_modes": _failure_modes(diagnostics_rows=diagnostics_rows, report=report, ledger=ledger),
        "diagnostic_scope": _diagnostic_scope(
            regime_name=regime_name,
            allowed_claim_level=allowed_claim_level,
            evidence_scope=str(ledger.get("evidence_scope", evidence_mode)),
            required_artifacts_present=required_artifacts_present,
        ),
    }


def _report_for_ledger(ledger: Mapping[str, Any], **updates: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = deepcopy(dict(ledger))
    for key, value in updates.items():
        resolved[key] = deepcopy(value)
    return resolved, build_claim_gate_report(resolved)


def _boundary_entry(
    *,
    name: str,
    ledger: Mapping[str, Any],
    updates: Mapping[str, Any],
    assumption: str,
    expected: str,
) -> dict[str, Any]:
    boundary_ledger, report = _report_for_ledger(ledger, **dict(updates))
    return _entry_from_report(
        regime_name=name,
        evidence_mode=str(boundary_ledger.get("evidence_mode", "ambiguous_metric")),
        structural_assumption=assumption,
        expected_selector_behavior="not_applicable_boundary_case",
        expected_diagnostic_behavior=expected,
        observed_diagnostic_behavior=report["summary"],
        ledger=boundary_ledger,
        report=report,
        diagnostics_rows=[],
    )


def build_proxy_regime_matrix_from_summary(
    summary: Mapping[str, Any],
    diagnostics_rows: Iterable[Mapping[str, Any]] = (),
    *,
    metric_bridge_rows: Iterable[Mapping[str, Any]] = (),
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_summary = deepcopy(dict(summary))
    diagnostics = [deepcopy(dict(row)) for row in diagnostics_rows]
    bridge_rows = [deepcopy(dict(row)) for row in metric_bridge_rows]
    bridge_overrides = _bridge_overrides_from_witnesses(bridge_rows)
    overrides = {
        **_matrix_evidence_overrides(evidence_overrides),
        **bridge_overrides,
    }
    ledger = build_evidence_ledger_from_summary(source_summary, **overrides)
    claim_report = build_claim_gate_report(ledger)
    grouped = _rows_by_regime(diagnostics)
    entries: list[dict[str, Any]] = []

    for regime_name in ("redundancy_dominated", "sparse_pairwise_synergy", "higher_order_synergy"):
        definition = REGIME_DEFINITIONS[regime_name]
        regime_rows = grouped.get(regime_name, [])
        regime_ledger, regime_report = _report_for_ledger(
            ledger,
            evidence_mode="synthetic_structural_only",
            evidence_scope="synthetic_structural_only",
            diagnostic_scope="synthetic_structural_only",
            diagnostic_claim_level="ambiguous_metric",
        )
        entries.append(
            _entry_from_report(
                regime_name=regime_name,
                evidence_mode="synthetic_structural_only",
                structural_assumption=definition["structural_assumption"],
                expected_selector_behavior=definition["expected_selector_behavior"],
                expected_diagnostic_behavior=definition["expected_diagnostic_behavior"],
                observed_diagnostic_behavior=_observed_behavior(regime_name, regime_rows),
                ledger=regime_ledger,
                report=regime_report,
                diagnostics_rows=regime_rows,
            )
        )

    entries.extend(
        [
            _boundary_entry(
                name="contamination_failed",
                ledger=ledger,
                updates={"contamination_status": "failed"},
                assumption="Contamination gate fails for the evidence package.",
                expected="Claim gate must force pilot_only.",
            ),
            _boundary_entry(
                name="missing_human_labels",
                ledger=ledger,
                updates={"human_labels_present": False},
                assumption="Human labels are absent or incomplete.",
                expected="measurement_validated must remain denied.",
            ),
            _boundary_entry(
                name="missing_kappa",
                ledger=ledger,
                updates={"kappa_present": False},
                assumption="Inter-annotator agreement evidence is absent.",
                expected="measurement_validated must remain denied.",
            ),
            _boundary_entry(
                name="stale_metric_bridge",
                ledger=ledger,
                updates={"bridge_freshness": "stale"},
                assumption="Metric bridge evidence is stale.",
                expected="Claims must not exceed operational_utility_only or ambiguous.",
            ),
            _boundary_entry(
                name="missing_metric_bridge",
                ledger=ledger,
                updates={"metric_bridge_witness_count": 0, "bridge_freshness": "missing"},
                assumption="MetricBridgeWitness evidence is missing.",
                expected="Claims must fail closed to ambiguous.",
            ),
            _boundary_entry(
                name="artifact_incomplete",
                ledger=ledger,
                updates={
                    "required_artifacts_present": False,
                    "projection_bundle_count": 0,
                    "missing_required_artifacts": ["projection_bundles"],
                },
                assumption="Required projection artifacts are incomplete.",
                expected="Claims must fail closed to ambiguous.",
            ),
        ]
    )

    entry_by_name = {entry["regime_name"]: entry for entry in entries}
    ordered_entries = [entry_by_name[name] for name in PROXY_REGIME_ENTRY_ORDER]
    return {
        "matrix_version": MATRIX_VERSION,
        "source_mode": "proxy_regime_diagnosis_matrix",
        "run_id": str(ledger.get("run_id", "")),
        "p04_status": str(ledger.get("p04_status", "BLOCKED_OPERATOR_REQUIRED")),
        "p09_status": str(ledger.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")),
        "allowed_claim_level": str(claim_report["allowed_claim_level"]),
        "denied_claims": list(claim_report["denied_claims"]),
        "reason_codes": list(claim_report["reason_codes"]),
        "reason_code_order": list(claim_report["reason_code_order"]),
        "diagnostic_scopes": list(DIAGNOSTIC_SCOPES),
        "denied_scope_values": list(DENIED_SCOPE_VALUES),
        "claim_boundary_warning": CLAIM_BOUNDARY_WARNING,
        "entries": ordered_entries,
    }


def build_proxy_regime_matrix_from_artifact_dir(
    artifact_dir: str | Path,
    *,
    run_id: str | None = None,
    **evidence_overrides: Any,
) -> dict[str, Any]:
    resolved_dir = Path(artifact_dir)
    summary_path = resolved_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"summary.json not found under {resolved_dir}")
    summary = _read_json(summary_path)
    diagnostics_rows = _read_jsonl(resolved_dir / "diagnostics.jsonl")
    metric_bridge_rows = _read_jsonl(resolved_dir / "metric_bridge_witnesses.jsonl")
    bridge_overrides = _bridge_overrides_from_witnesses(metric_bridge_rows)
    ledger_overrides = {
        **_matrix_evidence_overrides(evidence_overrides),
        **bridge_overrides,
    }
    ledger = build_evidence_ledger_from_artifact_dir(
        resolved_dir,
        run_id=run_id,
        **ledger_overrides,
    )
    merged_summary = {**summary, "artifact_counts": ledger["artifact_counts"], "run_id": ledger["run_id"]}
    return build_proxy_regime_matrix_from_summary(
        merged_summary,
        diagnostics_rows,
        metric_bridge_rows=metric_bridge_rows,
        evidence_overrides={
            **bridge_overrides,
            **evidence_overrides,
            "run_id": ledger["run_id"],
            "artifact_dir": str(resolved_dir.resolve()),
        },
    )


def format_proxy_regime_matrix_markdown(matrix: Mapping[str, Any]) -> str:
    lines = [
        "# Proxy-Regime Diagnosis Matrix",
        "",
        "## Claim Boundary",
        "",
        f"- {matrix['claim_boundary_warning']}",
        "- proxy-regime diagnosis is not deployed V-information certification.",
        "- measurement_validated is not claimed.",
        "",
        "## Matrix",
        "",
        "| Regime | Structural assumption | Expected behavior | Observed behavior | Allowed claim | Diagnostic scope | Reason codes |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in matrix.get("entries", []):
        reason_codes = ", ".join(entry.get("reason_codes", [])) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(entry["regime_name"]),
                    str(entry["structural_assumption"]),
                    str(entry["expected_diagnostic_behavior"]),
                    str(entry["observed_diagnostic_behavior"]),
                    str(entry["allowed_claim_level"]),
                    str(entry["diagnostic_scope"]),
                    reason_codes,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Denied Scope Values",
            "",
            *(f"- `{value}`" for value in matrix.get("denied_scope_values", [])),
            "",
        ]
    )
    return "\n".join(lines)


def write_proxy_regime_matrix(output_dir: str | Path, matrix: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(matrix))
    json_path = _stable_write_json(resolved_output_dir / "proxy_regime_matrix.json", payload)
    markdown_path = resolved_output_dir / "proxy_regime_matrix.md"
    markdown_path.write_text(format_proxy_regime_matrix_markdown(payload), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "proxy_regime_matrix_json": str(json_path),
        "proxy_regime_matrix_markdown": str(markdown_path),
    }
