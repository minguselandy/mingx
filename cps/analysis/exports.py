from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def ensure_directories(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def role_export_dir(export_dir: Path, model_role: str) -> Path:
    return export_dir / model_role


def question_export_dir(export_dir: Path, model_role: str, question_id: str) -> Path:
    return role_export_dir(export_dir, model_role) / "questions" / question_id


def question_export_manifest_path(export_dir: Path, model_role: str, question_id: str) -> Path:
    return question_export_dir(export_dir, model_role, question_id) / "export_manifest.json"


def export_delta_lcb(question_id: str, hop_depth: str, model_role: str, snapshot: dict, export_dir: Path) -> dict[str, str]:
    rows = [
        {
            "question_id": question_id,
            "hop_depth": hop_depth,
            "model_role": model_role,
            "paragraph_id": entry["paragraph_id"],
            "delta_loo_lcb": entry["delta_loo"],
        }
        for entry in snapshot["delta_loo_LCB"]
    ]
    export_question_dir = question_export_dir(export_dir, model_role, question_id)
    jsonl_path = write_jsonl(export_question_dir / "delta_loo_lcb.jsonl", rows)
    csv_path = write_csv(
        export_question_dir / "delta_loo_lcb.csv",
        rows,
        ["question_id", "hop_depth", "model_role", "paragraph_id", "delta_loo_lcb"],
    )
    bridge_input_path = write_csv(
        export_question_dir / "bridge_input.csv",
        rows,
        ["question_id", "hop_depth", "model_role", "paragraph_id", "delta_loo_lcb"],
    )
    export_manifest = write_json(
        question_export_manifest_path(export_dir, model_role, question_id),
        {
            "question_id": question_id,
            "model_role": model_role,
            "delta_loo_jsonl": str(jsonl_path),
            "delta_loo_csv": str(csv_path),
            "bridge_input": str(bridge_input_path),
            "row_count": len(rows),
        },
    )
    return {
        "delta_loo_jsonl": str(jsonl_path),
        "delta_loo_csv": str(csv_path),
        "bridge_input": str(bridge_input_path),
        "question_export_manifest": str(export_manifest),
    }


def export_stub_artifacts(export_dir: Path, question_id: str | None, mode: str = "smoke") -> dict[str, str]:
    if mode == "cohort":
        stubs = {
            "bridge_diagnostics": {
                "status": "pending_measurement_consumption",
                "question_scope": question_id or "cohort",
                "reason": "cohort measurements are ready, but bridge regression remains downstream",
            },
            "kappa_summary": {
                "status": "pending_measurement_consumption",
                "question_scope": question_id or "cohort",
                "reason": "annotation and expert arbitration remain outside the current cohort runner",
            },
            "tolerance_band": {
                "status": "pending_measurement_consumption",
                "question_scope": question_id or "cohort",
                "reason": "tolerance-band arbitration consumes bridged cohort-level delta_loo outputs",
            },
            "variance_bias_budget": {
                "status": "pending_measurement_consumption",
                "question_scope": question_id or "cohort",
                "reason": "variance and bias budget remain downstream of bridge and kappa computation",
            },
        }
    else:
        stubs = {
            "bridge_diagnostics": {
                "status": "not_computed",
                "question_id": question_id,
                "reason": "bridge regression is outside the current minimal Phase 1 smoke path",
            },
            "kappa_summary": {
                "status": "not_computed",
                "question_id": question_id,
                "reason": "annotation and expert arbitration are outside the current minimal Phase 1 smoke path",
            },
            "tolerance_band": {
                "status": "not_computed",
                "question_id": question_id,
                "reason": "tolerance-band arbitration requires bridged delta_loo across the cohort",
            },
            "variance_bias_budget": {
                "status": "mock",
                "question_id": question_id,
                "reason": "smoke run exports structure only; no cohort-level bridge or kappa variance yet",
            },
        }
    return {
        artifact_name: str(write_json(export_dir / f"{artifact_name}.json", payload))
        for artifact_name, payload in stubs.items()
    }
