from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class P56ReplayValidationError(ValueError):
    """Raised when P56 replay inputs or config cannot be parsed."""


PHASE = "P56"
TRACE_SCHEMA_VERSION = "p56_realistic_dispatch_trace.v1"
DEFAULT_CONFIG_PATH = Path("configs/runs/realistic-dispatch-replay-p56.json")
DEFAULT_CONTRACT_PATH = Path("docs/templates/diagnostic-threshold-contract-template.json")
COMMENT_LINE_PREFIXES = ("#", "//")

OUTPUT_ARTIFACTS = (
    "manifest.json",
    "claim_gate_report.json",
    "report.md",
)
TRACE_OUTPUT_ARTIFACTS = (
    "realistic_dispatch_replay_records.jsonl",
    "realistic_dispatch_replay_summary.csv",
)

DISPATCH_IDENTITY_FIELDS = (
    "run_id",
    "dispatch_id",
    "agent_id",
    "round_id",
)
REQUIRED_TRACE_FIELDS = (
    "run_id",
    "dispatch_id",
    "agent_id",
    "round_id",
    "candidate_pool_hash",
    "considered_candidate_ids",
    "selected_candidate_ids",
    "excluded_candidate_ids",
    "projection_plan_hash",
    "budget_witness_hash",
    "materialized_context_hash",
    "materialization_policy",
    "metric_bridge_witness_status",
    "metric_bridge_contract_id",
    "metric_bridge_active_stratum",
    "metric_bridge_freshness",
    "replay_intervention_id",
    "evaluator_policy",
    "metric_policy",
    "replicate_count",
    "effective_sample_size",
    "data_source_kind",
    "trace_schema_version",
)
OPTIONAL_TRACE_FIELDS = (
    "candidate_pool_items_hash",
    "candidate_pool_count",
    "selected_token_estimate",
    "realized_token_count",
    "budget_limit",
    "projection_bundle_hash",
    "source_trace_id",
    "operator_approval_ref",
    "contamination_status",
)
CLASSIFICATION_LABELS = (
    "replay_comparable",
    "replay_usable_metric_downgraded",
    "not_replay_comparable",
    "not_selector_comparable",
    "fail_closed_candidate_pool_mismatch",
    "fixture_only_engineering_evidence",
    "no_imported_traces",
)
FIXTURE_DATA_SOURCE_KINDS = {
    "fixture",
    "fixture_only",
    "fixture_test_only",
    "synthetic_fixture",
    "test_fixture",
}
FRESH_BRIDGE_VALUES = {"fresh"}
DOWNGRADE_BRIDGE_VALUES = {
    "ambiguous",
    "failed",
    "missing",
    "mismatched",
    "stale",
    "underpowered",
}
DENIED_CLAIMS = (
    "measurement_validation",
    "human_label_validation",
    "human_human_kappa",
    "deployed_v_information_verification",
    "theorem_level_deployed_submodularity_verification",
    "synthetic_evidence_as_bridge_evidence",
    "fixture_evidence_as_paper_grade_evidence",
    "replay_usability_as_metric_support",
    "replay_completeness_as_bridge_evidence",
    "extraction_audit_as_selector_validity",
    "reprojection_witness_as_deployed_runtime_improvement",
    "p55_no_row_report_as_bridge_support",
    "vinfo_proxy_supported_from_replay_only",
    "calibrated_proxy_supported_from_replay_only",
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _read_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise P56ReplayValidationError(f"JSON file does not exist: {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P56ReplayValidationError(f"JSON file must contain an object: {source}")
    return payload


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(payload), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def _path_reference(path: str | Path | None) -> str | None:
    if path is None:
        return None
    parsed = Path(path)
    if parsed.is_absolute():
        return parsed.name
    return parsed.as_posix()


def _payload_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_LINE_PREFIXES)


def detect_trace_file_status(path: str | Path | None) -> str:
    if path is None:
        return "absent"
    trace_path = Path(path)
    if not trace_path.exists():
        return "absent"
    if trace_path.suffix.lower() == ".jsonl":
        lines = trace_path.read_text(encoding="utf-8").splitlines()
        return "present" if any(_payload_line(line) for line in lines) else "empty"
    if trace_path.stat().st_size == 0:
        return "empty"
    return "present"


def load_trace_rows(path: str | Path) -> list[dict[str, Any]]:
    trace_path = Path(path)
    if not trace_path.exists():
        raise P56ReplayValidationError(f"trace input file does not exist: {trace_path}")
    if trace_path.suffix.lower() != ".jsonl":
        raise P56ReplayValidationError("P56 trace input must be a .jsonl file")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not _payload_line(line):
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise P56ReplayValidationError(f"line {line_number}: JSONL trace row must be an object")
        rows.append(payload)
    return rows


def compute_candidate_pool_hash(candidate_ids: Sequence[Any]) -> str:
    normalized = [str(candidate_id) for candidate_id in sorted(candidate_ids, key=str)]
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split("|") if part.strip()]
    return []


def _non_empty_string(value: Any) -> str | None:
    parsed = str(value).strip()
    return parsed or None


def _positive_number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _expected(config: Mapping[str, Any], key: str) -> str:
    value = config.get(key)
    if isinstance(value, Mapping):
        return str(value.get("policy_id") or value.get("contract_id") or value.get("kind") or "")
    return str(value or "")


def _expected_contract_id(config: Mapping[str, Any], contract: Mapping[str, Any]) -> str:
    configured = config.get("metric_bridge_contract_id")
    if configured:
        return str(configured)
    return str(contract.get("contract_id") or "diagnostic_threshold_contract_v12_template")


def _expected_active_stratum(config: Mapping[str, Any]) -> str:
    return str(config.get("active_stratum") or config.get("stratum_id") or "evidence_packet_selection_microtask_v1")


def _canonical_trace(raw: Mapping[str, Any], row_number: int) -> tuple[dict[str, Any], list[str]]:
    defects: list[str] = []
    missing = [field for field in REQUIRED_TRACE_FIELDS if field not in raw]
    defects.extend(f"row_{row_number}:missing_{field}" for field in missing)

    canonical: dict[str, Any] = {}
    for field in DISPATCH_IDENTITY_FIELDS:
        canonical[field] = _non_empty_string(raw.get(field))
        if canonical[field] is None:
            defects.append(f"row_{row_number}:{field}_empty")

    canonical["candidate_pool_hash"] = _non_empty_string(raw.get("candidate_pool_hash"))
    if canonical["candidate_pool_hash"] is None:
        defects.append(f"row_{row_number}:candidate_pool_hash_empty")

    canonical["considered_candidate_ids"] = _string_list(raw.get("considered_candidate_ids"))
    canonical["selected_candidate_ids"] = _string_list(raw.get("selected_candidate_ids"))
    canonical["excluded_candidate_ids"] = _string_list(raw.get("excluded_candidate_ids"))
    if not canonical["selected_candidate_ids"]:
        defects.append(f"row_{row_number}:selected_candidate_ids_empty")

    for field in (
        "projection_plan_hash",
        "budget_witness_hash",
        "materialized_context_hash",
        "materialization_policy",
        "metric_bridge_witness_status",
        "metric_bridge_contract_id",
        "metric_bridge_active_stratum",
        "metric_bridge_freshness",
        "replay_intervention_id",
        "evaluator_policy",
        "metric_policy",
        "data_source_kind",
        "trace_schema_version",
    ):
        canonical[field] = _non_empty_string(raw.get(field))
        if canonical[field] is None:
            defects.append(f"row_{row_number}:{field}_empty")

    for field in ("replicate_count", "effective_sample_size"):
        canonical[field] = _positive_number(raw.get(field))
        if canonical[field] is None:
            defects.append(f"row_{row_number}:{field}_not_positive_numeric")

    for field in OPTIONAL_TRACE_FIELDS:
        if field in raw:
            canonical[field] = raw[field]
    canonical["row_number"] = row_number
    return canonical, defects


def _policy_mismatches(row: Mapping[str, Any], config: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]:
    mismatches: list[str] = []
    expected_materialization = _expected(config, "materialization_policy")
    if expected_materialization and row.get("materialization_policy") != expected_materialization:
        mismatches.append("materialization_policy_mismatch")

    expected_evaluator = _expected(config, "evaluator_policy")
    if expected_evaluator and row.get("evaluator_policy") != expected_evaluator:
        mismatches.append("evaluator_policy_mismatch")

    expected_metric = _expected(config, "metric_policy")
    if expected_metric and row.get("metric_policy") != expected_metric:
        mismatches.append("metric_policy_mismatch")

    expected_contract = _expected_contract_id(config, contract)
    if expected_contract and row.get("metric_bridge_contract_id") != expected_contract:
        mismatches.append("metric_bridge_contract_id_mismatch")

    expected_stratum = _expected_active_stratum(config)
    if expected_stratum and row.get("metric_bridge_active_stratum") != expected_stratum:
        mismatches.append("metric_bridge_active_stratum_mismatch")

    expected_schema = str(config.get("trace_schema_version") or TRACE_SCHEMA_VERSION)
    if expected_schema and row.get("trace_schema_version") != expected_schema:
        mismatches.append("trace_schema_version_mismatch")
    return mismatches


def classify_trace(
    raw: Mapping[str, Any],
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    row_number: int = 1,
) -> dict[str, Any]:
    row, defects = _canonical_trace(raw, row_number)
    missing_identity = [field for field in DISPATCH_IDENTITY_FIELDS if not row.get(field)]
    data_source_kind = str(row.get("data_source_kind") or "")
    bridge_freshness = str(row.get("metric_bridge_freshness") or "missing")
    bridge_status = str(row.get("metric_bridge_witness_status") or "missing")
    considered_ids = list(row.get("considered_candidate_ids") or [])
    selected_ids = list(row.get("selected_candidate_ids") or [])
    expected_hash = compute_candidate_pool_hash(considered_ids) if considered_ids else None
    candidate_pool_mismatch = bool(
        considered_ids
        and row.get("candidate_pool_hash")
        and row.get("candidate_pool_hash") != expected_hash
    )
    policy_mismatches = _policy_mismatches(row, config, contract)
    defects.extend(f"row_{row_number}:{mismatch}" for mismatch in policy_mismatches)

    if missing_identity:
        classification = "not_replay_comparable"
        reason_codes = ["missing_dispatch_identity"]
    elif selected_ids and not considered_ids:
        classification = "not_selector_comparable"
        reason_codes = ["selected_only_trace"]
    elif candidate_pool_mismatch:
        classification = "fail_closed_candidate_pool_mismatch"
        reason_codes = ["candidate_pool_hash_mismatch"]
    elif data_source_kind in FIXTURE_DATA_SOURCE_KINDS:
        classification = "fixture_only_engineering_evidence"
        reason_codes = ["fixture_only_trace"]
    elif policy_mismatches:
        classification = "replay_usable_metric_downgraded"
        reason_codes = ["policy_or_bridge_contract_mismatch"]
    elif bridge_freshness not in FRESH_BRIDGE_VALUES or bridge_status != "present":
        classification = "replay_usable_metric_downgraded"
        normalized_bridge = bridge_freshness if bridge_freshness in DOWNGRADE_BRIDGE_VALUES else "ambiguous"
        reason_codes = [f"metric_bridge_{normalized_bridge}"]
    else:
        classification = "replay_comparable"
        reason_codes = ["complete_trace_fresh_matching_bridge"]

    if not considered_ids and "selected_only_trace" not in reason_codes:
        reason_codes.append("considered_candidate_set_missing")
    if not row.get("projection_plan_hash"):
        reason_codes.append("projection_plan_missing")
    if not row.get("budget_witness_hash"):
        reason_codes.append("budget_witness_missing")
    if not row.get("materialized_context_hash"):
        reason_codes.append("materialized_context_missing")

    return {
        "row_number": row_number,
        "run_id": row.get("run_id"),
        "dispatch_id": row.get("dispatch_id"),
        "agent_id": row.get("agent_id"),
        "round_id": row.get("round_id"),
        "classification": classification,
        "reason_codes": sorted(set(reason_codes)),
        "validation_defects": sorted(set(defects)),
        "candidate_pool_hash_status": "mismatch" if candidate_pool_mismatch else "matched",
        "expected_candidate_pool_hash": expected_hash,
        "metric_bridge_witness_status": bridge_status,
        "metric_bridge_freshness": bridge_freshness,
        "metric_bridge_active_stratum": row.get("metric_bridge_active_stratum"),
        "data_source_kind": data_source_kind,
        "effective_sample_size": row.get("effective_sample_size"),
        "replicate_count": row.get("replicate_count"),
    }


def derive_replay_claim_gate(
    records: Sequence[Mapping[str, Any]],
    *,
    trace_file_status: str,
    traces_imported: int,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    classification_counts = Counter(record["classification"] for record in records)
    for label in CLASSIFICATION_LABELS:
        classification_counts.setdefault(label, 0)
    bridge_counts = Counter(str(record.get("metric_bridge_freshness") or "missing") for record in records)
    if traces_imported == 0:
        classification_counts["no_imported_traces"] = 1
        bridge_counts["missing"] = 1

    trace_validation_failures = [
        defect
        for record in records
        for defect in record.get("validation_defects", [])
    ]
    no_imported_traces = traces_imported == 0
    validated_records = [
        record
        for record in records
        if record["classification"] in {
            "replay_comparable",
            "replay_usable_metric_downgraded",
            "fixture_only_engineering_evidence",
        }
        and not record.get("validation_defects")
    ]

    if no_imported_traces:
        claim_gate_result = "no_imported_traces"
        reason_codes = ["no_imported_traces", "operator_traces_required", "p55_blocked_state_preserved"]
        requires_operator = True
    else:
        claim_gate_result = "replay_scaffold_fail_closed"
        reason_codes = ["replay_usability_is_not_metric_support", "metric_bridge_review_required"]
        requires_operator = False
        if classification_counts["fail_closed_candidate_pool_mismatch"]:
            reason_codes.append("candidate_pool_hash_mismatch")
        if classification_counts["not_selector_comparable"]:
            reason_codes.append("selected_only_not_selector_comparable")
        if classification_counts["not_replay_comparable"]:
            reason_codes.append("not_replay_comparable")
        if classification_counts["fixture_only_engineering_evidence"]:
            reason_codes.append("fixture_only_paper_ineligible")

    data_source_kinds = sorted({str(record.get("data_source_kind") or "missing") for record in records})
    if not data_source_kinds:
        data_source_kinds = [str(config.get("data_source_kind") or "operator_imported_traces")]

    return {
        "phase": PHASE,
        "claim_gate_result": claim_gate_result,
        "data_source_kind": data_source_kinds[0] if len(data_source_kinds) == 1 else "mixed",
        "data_source_kinds": data_source_kinds,
        "trace_file_status": trace_file_status,
        "traces_imported": traces_imported,
        "traces_validated": len(validated_records),
        "trace_validation_failures": sorted(set(trace_validation_failures)),
        "replay_classification_counts": dict(sorted(classification_counts.items())),
        "metric_bridge_status_counts": dict(sorted(bridge_counts.items())),
        "candidate_pool_mismatch_count": int(classification_counts["fail_closed_candidate_pool_mismatch"]),
        "selected_only_count": int(classification_counts["not_selector_comparable"]),
        "metric_claim_level": "ambiguous_metric",
        "selector_regime_label": "none",
        "review_ceiling": "none",
        "paper_evidence_eligible": False,
        "measurement_validation_claim": False,
        "vinfo_proxy_supported_allowed": False,
        "calibrated_proxy_supported_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "blocked_operator_required": bool(no_imported_traces),
        "requires_operator": requires_operator,
        "next_phase_allowed": False,
        "p55_blocked_state_preserved": True,
        "reason_codes": sorted(set(reason_codes)),
    }


def _manifest(report: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "artifact_set": "p56_realistic_dispatch_replay",
        "canonical_outputs": list(OUTPUT_ARTIFACTS),
        "conditional_outputs": list(TRACE_OUTPUT_ARTIFACTS) if report["records"] else [],
        "config_reference": _path_reference(config.get("_config_path")),
        "input_traces_reference": _path_reference(config.get("input_traces_path")),
        "output_reference": _path_reference(config.get("output_dir")),
        "claim_gate_result": report["claim_gate_result"],
        "trace_file_status": report["trace_file_status"],
        "traces_imported": report["traces_imported"],
        "traces_validated": report["traces_validated"],
        "paper_evidence_eligible": report["paper_evidence_eligible"],
        "measurement_validation_claim": report["measurement_validation_claim"],
        "vinfo_proxy_supported_allowed": report["vinfo_proxy_supported_allowed"],
        "calibrated_proxy_supported_allowed": report["calibrated_proxy_supported_allowed"],
        "next_phase_allowed": report["next_phase_allowed"],
    }


def _markdown_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# P56 Realistic Dispatch Replay Report",
        "",
        "## Summary",
        "",
        f"- Claim gate result: `{report['claim_gate_result']}`",
        f"- Trace file status: `{report['trace_file_status']}`",
        f"- Traces imported: `{report['traces_imported']}`",
        f"- Traces validated: `{report['traces_validated']}`",
        f"- Metric claim level: `{report['metric_claim_level']}`",
        f"- Paper evidence eligible: `{str(report['paper_evidence_eligible']).lower()}`",
        f"- Measurement validation claim: `{str(report['measurement_validation_claim']).lower()}`",
        f"- vinfo_proxy_supported allowed: `{str(report['vinfo_proxy_supported_allowed']).lower()}`",
        f"- calibrated_proxy_supported allowed: `{str(report['calibrated_proxy_supported_allowed']).lower()}`",
        "",
        "## Replay Classification Counts",
        "",
    ]
    for label, count in report["replay_classification_counts"].items():
        lines.append(f"- `{label}`: {count}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Replay usability is not metric support.",
            "Replay completeness is not bridge evidence.",
            "P56 does not proceed from P55 success, and P55 remains blocked pending contract-compliant operator-imported rows.",
            "Fresh matching MetricBridgeWitness status is required before any metric claim inheritance, and this P56 scaffold does not emit bridge support.",
            "",
        ]
    )
    return "\n".join(lines)


def write_p56_outputs(report: Mapping[str, Any], output_dir: str | Path, config: Mapping[str, Any]) -> list[str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_json(destination / "manifest.json", _manifest(report, config))
    _write_json(destination / "claim_gate_report.json", report)
    (destination / "report.md").write_text(_markdown_report(report), encoding="utf-8")

    artifact_names = list(OUTPUT_ARTIFACTS)
    if report["records"]:
        _write_jsonl(destination / "realistic_dispatch_replay_records.jsonl", report["records"])
        summary_rows = [
            {"classification": label, "count": count}
            for label, count in report["replay_classification_counts"].items()
        ]
        _write_csv(
            destination / "realistic_dispatch_replay_summary.csv",
            summary_rows,
            ["classification", "count"],
        )
        artifact_names.extend(TRACE_OUTPUT_ARTIFACTS)
    return sorted(artifact_names)


def run_p56_realistic_dispatch_replay(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = _read_json(config_path)
    contract = _read_json(contract_path)
    config["_config_path"] = str(config_path)
    if output_dir is not None:
        config["output_dir"] = str(output_dir)

    trace_path = Path(str(config["input_traces_path"]))
    trace_file_status = detect_trace_file_status(trace_path)
    rows = load_trace_rows(trace_path) if trace_file_status == "present" else []
    records = [
        classify_trace(row, config, contract, row_number=index)
        for index, row in enumerate(rows, start=1)
    ]
    records.sort(
        key=lambda record: (
            str(record.get("run_id") or ""),
            str(record.get("dispatch_id") or ""),
            str(record.get("agent_id") or ""),
            str(record.get("round_id") or ""),
            int(record.get("row_number") or 0),
        )
    )

    report = derive_replay_claim_gate(
        records,
        trace_file_status=trace_file_status,
        traces_imported=len(rows),
        config=config,
    )
    report["records"] = records
    report["output_artifacts"] = write_p56_outputs(report, config["output_dir"], config)
    report["output_dir"] = str(Path(config["output_dir"]))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the P56 realistic dispatch replay scaffold.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    report = run_p56_realistic_dispatch_replay(
        config_path=args.config,
        contract_path=args.contract,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "claim_gate_result": report["claim_gate_result"],
                "trace_file_status": report["trace_file_status"],
                "traces_imported": report["traces_imported"],
                "traces_validated": report["traces_validated"],
                "metric_claim_level": report["metric_claim_level"],
                "paper_evidence_eligible": report["paper_evidence_eligible"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
