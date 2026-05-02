from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.artifacts import rebuild_projection_summary_from_events


REQUIRED_EVIDENCE_ARTIFACTS = (
    "candidate_pools",
    "projection_plans",
    "budget_witnesses",
    "materialized_contexts",
    "metric_bridge_witnesses",
    "diagnostics",
    "projection_bundles",
)
REQUIRED_ARTIFACTS = REQUIRED_EVIDENCE_ARTIFACTS
ARTIFACT_JSONL_FILENAMES = {
    "candidate_pools": "candidate_pools.jsonl",
    "projection_plans": "projection_plans.jsonl",
    "budget_witnesses": "budget_witnesses.jsonl",
    "materialized_contexts": "materialized_contexts.jsonl",
    "metric_bridge_witnesses": "metric_bridge_witnesses.jsonl",
    "diagnostics": "diagnostics.jsonl",
    "projection_bundles": "projection_bundles.jsonl",
}
DEFAULT_P04_STATUS = "BLOCKED_OPERATOR_REQUIRED"
DEFAULT_P09_STATUS = "BLOCKED_OPERATOR_REQUIRED"


def _stable_write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _artifact_counts(summary: Mapping[str, Any]) -> dict[str, int]:
    counts = dict(summary.get("artifact_counts") or {})
    return {key: int(counts.get(key, 0) or 0) for key in REQUIRED_EVIDENCE_ARTIFACTS}


def _artifact_file_counts(artifact_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, filename in ARTIFACT_JSONL_FILENAMES.items():
        path = artifact_dir / filename
        counts[key] = len(_read_jsonl(path)) if path.exists() else 0
    return counts


def _missing_required_artifacts(
    *,
    artifact_counts: Mapping[str, int],
    dispatch_count: int,
) -> list[str]:
    expected_count = max(1, int(dispatch_count))
    missing: list[str] = []
    for key in REQUIRED_EVIDENCE_ARTIFACTS:
        count = int(artifact_counts.get(key, 0) or 0)
        if count <= 0 or (dispatch_count > 0 and count != expected_count):
            missing.append(key)
    return missing


def _infer_evidence_mode(summary: Mapping[str, Any], overrides: Mapping[str, Any]) -> str:
    if overrides.get("evidence_mode"):
        return str(overrides["evidence_mode"])
    if summary.get("evidence_mode"):
        return str(summary["evidence_mode"])
    claim_level = str(summary.get("claim_level") or "")
    if claim_level:
        return claim_level
    metric_claims = set((summary.get("metric_claim_level_counts") or {}).keys())
    if "engineering_smoke_only" in metric_claims:
        return "engineering_smoke_only"
    if "structural_synthetic_only" in metric_claims:
        return "synthetic_structural_only"
    if summary.get("complete_artifact_sets"):
        return "replayable_artifact_evidence"
    return "ambiguous"


def _infer_source_phase(summary: Mapping[str, Any], overrides: Mapping[str, Any], evidence_mode: str) -> str:
    if overrides.get("source_phase"):
        return str(overrides["source_phase"])
    if summary.get("source_phase"):
        return str(summary["source_phase"])
    if evidence_mode == "engineering_smoke_only":
        return "P11"
    if evidence_mode == "synthetic_structural_only":
        return "P05"
    return "unknown"


def _complete_artifact_sets(artifact_counts: Mapping[str, int]) -> bool:
    required_counts = tuple(int(artifact_counts.get(key, 0) or 0) for key in REQUIRED_EVIDENCE_ARTIFACTS)
    return len(set(required_counts)) == 1 and required_counts[0] > 0


def _bundle_hashes_from_dir(artifact_dir: Path) -> list[str]:
    rows = _read_jsonl(artifact_dir / "projection_bundles.jsonl")
    hashes = {str(row["canonical_hash"]) for row in rows if row.get("canonical_hash")}
    return sorted(hashes)


def build_evidence_ledger_from_summary(
    summary: Mapping[str, Any],
    **overrides: Any,
) -> dict[str, Any]:
    source = deepcopy(dict(summary))
    override_payload = deepcopy(dict(overrides))
    artifact_counts = _artifact_counts(source)
    dispatch_count = int(source.get("dispatch_count", 0) or 0)
    missing_required_artifacts = _missing_required_artifacts(
        artifact_counts=artifact_counts,
        dispatch_count=dispatch_count,
    )
    projection_bundle_hashes = sorted(
        str(value)
        for value in override_payload.pop("projection_bundle_hashes", source.get("projection_bundle_hashes", [])) or []
    )
    required_artifacts_present = not missing_required_artifacts and _complete_artifact_sets(artifact_counts)
    evidence_mode = _infer_evidence_mode(source, override_payload)
    source_phase = _infer_source_phase(source, override_payload, evidence_mode)

    ledger: dict[str, Any] = {
        "run_id": str(override_payload.pop("run_id", source.get("run_id", ""))),
        "evidence_mode": evidence_mode,
        "source_phase": source_phase,
        "source_of_truth": str(source.get("source_of_truth", "summary")),
        "dispatch_count": dispatch_count,
        "artifact_counts": {key: artifact_counts[key] for key in REQUIRED_EVIDENCE_ARTIFACTS},
        "required_artifacts": list(REQUIRED_EVIDENCE_ARTIFACTS),
        "required_artifacts_present": required_artifacts_present,
        "missing_required_artifacts": missing_required_artifacts,
        "projection_bundle_count": int(artifact_counts["projection_bundles"]),
        "projection_bundle_hashes": projection_bundle_hashes,
        "projection_bundle_hashes_present": bool(projection_bundle_hashes)
        and int(artifact_counts["projection_bundles"]) == len(projection_bundle_hashes),
        "metric_bridge_witness_count": int(artifact_counts["metric_bridge_witnesses"]),
        "diagnostic_count": int(artifact_counts["diagnostics"]),
        "contamination_status": str(
            override_payload.pop("contamination_status", source.get("contamination_status", "unknown"))
        ),
        "human_labels_present": bool(
            override_payload.pop("human_labels_present", source.get("human_labels_present", False))
        ),
        "kappa_present": bool(override_payload.pop("kappa_present", source.get("kappa_present", False))),
        "bridge_freshness": str(
            override_payload.pop("bridge_freshness", source.get("bridge_freshness", "missing"))
        ),
        "replay_available": bool(required_artifacts_present and int(artifact_counts["projection_bundles"]) > 0),
        "live_api_used": bool(override_payload.pop("live_api_used", source.get("live_api_used", False))),
        "external_runtime_used": bool(
            override_payload.pop("external_runtime_used", source.get("external_runtime_used", False))
        ),
        "p04_status": str(override_payload.pop("p04_status", source.get("p04_status", DEFAULT_P04_STATUS))),
        "p09_status": str(override_payload.pop("p09_status", source.get("p09_status", DEFAULT_P09_STATUS))),
        "metric_claim_level_counts": dict(sorted((source.get("metric_claim_level_counts") or {}).items())),
        "selector_action_counts": dict(sorted((source.get("selector_action_counts") or {}).items())),
    }
    for key, value in sorted(override_payload.items()):
        ledger[key] = deepcopy(value)
    return ledger


def build_evidence_ledger_from_artifact_dir(
    artifact_dir: str | Path,
    *,
    run_id: str | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    resolved_dir = Path(artifact_dir)
    summary_json: dict[str, Any] = {}
    if (resolved_dir / "summary.json").exists():
        summary_json = json.loads((resolved_dir / "summary.json").read_text(encoding="utf-8"))
    selected_run_id = run_id or summary_json.get("run_id")
    if (resolved_dir / "events.jsonl").exists():
        event_summary = rebuild_projection_summary_from_events(resolved_dir, run_id=selected_run_id)
        summary = {**summary_json, **event_summary, "run_id": selected_run_id or event_summary.get("run_id")}
        if summary_json.get("claim_level"):
            summary["claim_level"] = summary_json["claim_level"]
        if summary_json.get("evidence_mode"):
            summary["evidence_mode"] = summary_json["evidence_mode"]
    elif summary_json:
        summary = summary_json
    else:
        raise FileNotFoundError(f"no events.jsonl or summary.json found under {resolved_dir}")
    file_counts = _artifact_file_counts(resolved_dir)
    if any((resolved_dir / filename).exists() for filename in ARTIFACT_JSONL_FILENAMES.values()):
        summary = {**summary, "artifact_counts": file_counts}
        summary["dispatch_count"] = int(summary.get("dispatch_count", 0) or max(file_counts.values(), default=0))
    bundle_hashes = _bundle_hashes_from_dir(resolved_dir)
    return build_evidence_ledger_from_summary(
        summary,
        projection_bundle_hashes=bundle_hashes,
        artifact_dir=str(resolved_dir.resolve()),
        **overrides,
    )


def write_evidence_ledger(path: str | Path, ledger: Mapping[str, Any]) -> Path:
    return _stable_write_json(path, deepcopy(dict(ledger)))
