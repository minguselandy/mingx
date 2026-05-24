from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cps.schema import ProjectionBundleV1, projection_bundle_from_epf_final_metadata

DEFAULT_CONFIG = ROOT / "configs" / "post_lapi" / "artifact_replay_integrity_config.yaml"

RAW_RESPONSE_BODY_FIELDS = {
    "raw_api_response",
    "raw_api_response_body",
    "raw_api_response_payload",
    "raw_body",
    "raw_response",
    "raw_response_body",
    "raw_response_payload",
}
RAW_RESPONSE_FLAG_FIELDS = {
    "raw_api_responses_stored",
    "raw_response_stored",
    "store_raw_api_response",
}


def _normalize(value: Any) -> str:
    text = str(value).strip().lower()
    for char in (" ", "-", "/"):
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_from_root(path_text: str) -> Path:
    return (ROOT / path_text).resolve()


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _assert_allowed_path(path: Path, exclude_roots: Iterable[str]) -> None:
    for exclude_root in exclude_roots:
        excluded = _path_from_root(exclude_root)
        if _is_under(path, excluded):
            raise ValueError(f"excluded path is not audit-eligible: {_relative(path)}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _walk(value: Any, *, path: str = "payload") -> Iterable[tuple[str, Any, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, key, child
            yield from _walk(child, path=child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, index, child
            yield from _walk(child, path=child_path)


def _has_record(payload: Mapping[str, Any], record_name: str) -> bool:
    return isinstance(payload.get(record_name), Mapping)


def _has_nested_field(payload: Mapping[str, Any], record_name: str, field_name: str) -> bool:
    record = payload.get(record_name)
    return isinstance(record, Mapping) and field_name in record and record[field_name] not in (None, "")


def _raw_response_policy_passes(payload: Mapping[str, Any]) -> bool:
    saw_raw_false = False
    for _, key, value in _walk(payload):
        normalized_key = _normalize(key)
        if normalized_key in RAW_RESPONSE_BODY_FIELDS:
            return False
        if normalized_key in RAW_RESPONSE_FLAG_FIELDS:
            if value is not False:
                return False
            saw_raw_false = True
    return saw_raw_false


def _denied_claim_leakage_count(payload: Mapping[str, Any], config: Mapping[str, Any]) -> int:
    denied_claims = {_normalize(value) for value in config["denied_claims"]}
    forbidden_true_fields = {_normalize(value) for value in config["forbidden_true_fields"]}
    count = 0
    for _, key, value in _walk(payload):
        normalized_key = _normalize(key)
        if normalized_key in forbidden_true_fields and value is True:
            count += 1
        if normalized_key == "allowed_claims" and isinstance(value, list):
            count += sum(1 for item in value if _normalize(item) in denied_claims)
        if normalized_key in {"metric_claim_level", "diagnostic_claim_level", "current_claim_level"}:
            if _normalize(value) in denied_claims:
                count += 1
    return count


def _claim_boundary_consistent(payload: Mapping[str, Any], config: Mapping[str, Any]) -> bool:
    claim_ledger = payload.get("claim_ledger")
    if not isinstance(claim_ledger, Mapping):
        return False
    if claim_ledger.get("current_claim_level") != config["claim_level"]:
        return False
    if claim_ledger.get("claim_upgrade") is not False:
        return False
    if claim_ledger.get("route_5_locked") is not True:
        return False
    if claim_ledger.get("route_8_locked") is not True:
        return False
    if claim_ledger.get("raw_response_stored") is not False:
        return False
    return _denied_claim_leakage_count(payload, config) == 0


def _replay_reconstruction_passes(payload: Mapping[str, Any]) -> bool:
    projection_plan = payload.get("projection_plan")
    materialized_context = payload.get("materialized_context")
    if not isinstance(projection_plan, Mapping) or not isinstance(materialized_context, Mapping):
        return False
    considered = set(projection_plan.get("candidate_ids_considered") or [])
    selected = set(projection_plan.get("selected_evidence_ids") or [])
    excluded = set(projection_plan.get("excluded_evidence_ids") or [])
    materialization_order = list(materialized_context.get("materialization_order") or [])
    evidence_hashes = materialized_context.get("evidence_hashes") or {}
    if selected & excluded:
        return False
    if not selected.issubset(considered):
        return False
    if not excluded.issubset(considered):
        return False
    if materialization_order != list(projection_plan.get("selected_evidence_ids") or []):
        return False
    return all(item in evidence_hashes for item in selected)


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _bundle_from_source(source: Mapping[str, Any]) -> ProjectionBundleV1:
    kind = source.get("kind")
    if kind != "epf_final_metadata":
        raise ValueError(f"unsupported bundle source kind: {kind}")
    return projection_bundle_from_epf_final_metadata(
        final_manifest=_load_json(_path_from_root(str(source["final_manifest"]))),
        final_claim_request=_load_json(_path_from_root(str(source["final_claim_request"]))),
        scoped_operational_evaluation_summary=_load_json(
            _path_from_root(str(source["scoped_operational_evaluation_summary"]))
        ),
    )


def _supporting_artifact_rows(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path_text in config["supporting_artifacts"]:
        path = _path_from_root(str(path_text))
        _assert_allowed_path(path, config["exclude_roots"])
        rows.append(
            {
                "path": _relative(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": _sha256(path) if path.exists() and path.is_file() else None,
            }
        )
    return rows


def _bundle_rows(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in config["bundle_sources"]:
        for source_path_key in ("final_manifest", "final_claim_request", "scoped_operational_evaluation_summary"):
            _assert_allowed_path(_path_from_root(str(source[source_path_key])), config["exclude_roots"])
        bundle_id = str(source["bundle_id"])
        try:
            bundle = _bundle_from_source(source)
            payload = bundle.to_dict()
            ProjectionBundleV1.from_dict(payload)
            schema_valid = True
            validation_error = None
        except Exception as exc:  # noqa: BLE001 - audit row records failure instead of hiding it.
            payload = {}
            schema_valid = False
            validation_error = str(exc)
        row: dict[str, Any] = {
            "bundle_id": bundle_id,
            "source_kind": source["kind"],
            "schema_valid": schema_valid,
            "validation_error": validation_error,
        }
        for record_name in config["required_records"]:
            row[f"{record_name}_present"] = _has_record(payload, record_name)
        for record_name, fields in config["required_fields"].items():
            for field_name in fields:
                row[f"{record_name}.{field_name}_present"] = _has_nested_field(payload, record_name, field_name)
        row["selected_evidence_ids_present"] = _has_nested_field(payload, "projection_plan", "selected_evidence_ids")
        row["excluded_evidence_ids_present"] = _has_nested_field(payload, "projection_plan", "excluded_evidence_ids")
        row["materialization_order_present"] = _has_nested_field(
            payload,
            "materialized_context",
            "materialization_order",
        )
        row["downstream_prompt_hash_present"] = _has_nested_field(
            payload,
            "materialized_context",
            "downstream_prompt_hash",
        )
        row["model_snapshot_present"] = _has_nested_field(payload, "metric_bridge_witness", "model_snapshot")
        row["endpoint_present"] = _has_nested_field(payload, "metric_bridge_witness", "endpoint")
        row["raw_response_stored_false"] = _raw_response_policy_passes(payload)
        row["replay_reconstruction_pass"] = _replay_reconstruction_passes(payload)
        row["claim_boundary_consistent"] = _claim_boundary_consistent(payload, config)
        row["denied_claim_leakage_count"] = _denied_claim_leakage_count(payload, config)
        row["canonical_hash"] = bundle.canonical_hash() if schema_valid else None
        rows.append(row)
    return rows


def _summary(config: Mapping[str, Any], bundles: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    bundle_count = len(bundles)
    schema_valid_count = sum(1 for row in bundles if row["schema_valid"])
    projection_plan_count = sum(1 for row in bundles if row["projection_plan_present"])
    budget_witness_count = sum(1 for row in bundles if row["budget_witness_present"])
    materialized_context_count = sum(1 for row in bundles if row["materialized_context_present"])
    metric_bridge_witness_count = sum(1 for row in bundles if row["metric_bridge_witness_present"])
    claim_ledger_count = sum(1 for row in bundles if row["claim_ledger_present"])
    selected_count = sum(1 for row in bundles if row["selected_evidence_ids_present"])
    excluded_count = sum(1 for row in bundles if row["excluded_evidence_ids_present"])
    materialization_order_count = sum(1 for row in bundles if row["materialization_order_present"])
    downstream_prompt_hash_count = sum(1 for row in bundles if row["downstream_prompt_hash_present"])
    model_snapshot_endpoint_count = sum(
        1 for row in bundles if row["model_snapshot_present"] and row["endpoint_present"]
    )
    raw_false_count = sum(1 for row in bundles if row["raw_response_stored_false"])
    replay_pass_count = sum(1 for row in bundles if row["replay_reconstruction_pass"])
    claim_boundary_count = sum(1 for row in bundles if row["claim_boundary_consistent"])
    denied_leakage_count = sum(int(row["denied_claim_leakage_count"]) for row in bundles)
    artifact_exists_count = sum(1 for row in artifacts if row["exists"])
    metrics = {
        "bundle_count": bundle_count,
        "schema_valid_count": schema_valid_count,
        "schema_valid_rate": _rate(schema_valid_count, bundle_count),
        "projection_plan_present_count": projection_plan_count,
        "projection_plan_present_rate": _rate(projection_plan_count, bundle_count),
        "budget_witness_present_count": budget_witness_count,
        "budget_witness_present_rate": _rate(budget_witness_count, bundle_count),
        "materialized_context_present_count": materialized_context_count,
        "materialized_context_present_rate": _rate(materialized_context_count, bundle_count),
        "metric_bridge_witness_present_count": metric_bridge_witness_count,
        "metric_bridge_witness_present_rate": _rate(metric_bridge_witness_count, bundle_count),
        "claim_ledger_present_count": claim_ledger_count,
        "claim_ledger_present_rate": _rate(claim_ledger_count, bundle_count),
        "selected_evidence_ids_present_count": selected_count,
        "selected_evidence_ids_present_rate": _rate(selected_count, bundle_count),
        "excluded_evidence_ids_present_count": excluded_count,
        "excluded_evidence_ids_present_rate": _rate(excluded_count, bundle_count),
        "materialization_order_present_count": materialization_order_count,
        "materialization_order_present_rate": _rate(materialization_order_count, bundle_count),
        "downstream_prompt_hash_present_count": downstream_prompt_hash_count,
        "downstream_prompt_hash_present_rate": _rate(downstream_prompt_hash_count, bundle_count),
        "model_snapshot_endpoint_present_count": model_snapshot_endpoint_count,
        "model_snapshot_endpoint_present_rate": _rate(model_snapshot_endpoint_count, bundle_count),
        "raw_response_stored_false_count": raw_false_count,
        "raw_response_stored_false_rate": _rate(raw_false_count, bundle_count),
        "replay_reconstruction_pass_count": replay_pass_count,
        "replay_reconstruction_pass_rate": _rate(replay_pass_count, bundle_count),
        "claim_boundary_consistency_count": claim_boundary_count,
        "claim_boundary_consistency_rate": _rate(claim_boundary_count, bundle_count),
        "denied_claim_leakage_count": denied_leakage_count,
        "supporting_artifact_count": len(artifacts),
        "supporting_artifact_exists_count": artifact_exists_count,
        "supporting_artifact_exists_rate": _rate(artifact_exists_count, len(artifacts)),
    }
    return {
        "audit_id": config["audit_id"],
        "claim_level": config["claim_level"],
        "live_api_calls_run": False,
        "new_experiments_run": False,
        "raw_api_responses_stored": False,
        "claim_upgrade_introduced": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "allowed_claims": config["allowed_claims"],
        "denied_claims": config["denied_claims"],
        "metrics": metrics,
        "bundles": bundles,
        "supporting_artifacts": artifacts,
    }


def _write_outputs(summary: Mapping[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    csv_path = output_dir / "summary.csv"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics = dict(summary["metrics"])
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics))
        writer.writeheader()
        writer.writerow(metrics)


def run(config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    if config.get("live_api_calls_allowed") is not False:
        raise ValueError("POST-LAPI replay integrity audit must not allow live API calls")
    if config.get("new_experiments_allowed") is not False:
        raise ValueError("POST-LAPI replay integrity audit must not allow new experiments")
    if config.get("raw_response_storage_allowed") is not False:
        raise ValueError("POST-LAPI replay integrity audit must not allow raw response storage")
    bundles = _bundle_rows(config)
    artifacts = _supporting_artifact_rows(config)
    summary = _summary(config, bundles, artifacts)
    _write_outputs(summary, _path_from_root(str(config["output_dir"])))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit POST-LAPI projection-bundle replay integrity offline.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="JSON-compatible YAML audit config path")
    args = parser.parse_args()
    summary = run(_path_from_root(args.config) if not Path(args.config).is_absolute() else Path(args.config))
    metrics = summary["metrics"]
    print(
        "POST-LAPI replay integrity audit complete: "
        f"bundle_count={metrics['bundle_count']}, "
        f"schema_valid_count={metrics['schema_valid_count']}, "
        f"denied_claim_leakage_count={metrics['denied_claim_leakage_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
