from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cps.analysis.exports import ensure_directories, write_json, write_text
from cps.data.manifest import load_manifest
from cps.runtime.calibration import build_calibration_payload
from cps.runtime.cohort import _blocked_questions_path, _read_blocked_question_ids


FOLLOWUP_PACKAGE_VERSION = "phase1_followup_package_v1"


def _resolve_plan_path_value(
    plan: dict[str, Any],
    key: str,
    *,
    plan_path: Path,
    root_dir: Path | None = None,
    default: str | None = None,
) -> Path:
    raw_value = plan.get(key, default)
    if raw_value is None:
        raise KeyError(f"missing required plan field: {key}")
    path = Path(str(raw_value))
    if path.is_absolute():
        return path.resolve()
    local_candidate = (plan_path.parent / path).resolve()
    if local_candidate.exists():
        return local_candidate
    base_dir = (root_dir or Path.cwd()).resolve()
    return (base_dir / path).resolve()


def _selected_by_hop(payload: dict[str, Any]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for entry in payload.get("selected_questions") or ():
        grouped[str(entry["hop_depth"])].append(str(entry["question_id"]))
    return {hop_depth: values for hop_depth, values in sorted(grouped.items())}


def _selected_question_ids(payload: dict[str, Any]) -> list[str]:
    return [str(entry["question_id"]) for entry in payload.get("selected_questions") or ()]


def _followup_readme(
    *,
    source_plan_path: Path,
    decision_sheet_path: Path | None,
    dropped_question_ids: list[str],
    followup_plan_path: Path,
    blocked_questions_path: Path,
    calibration_manifest_path: Path,
) -> str:
    decision_line = (
        f"- Decision sheet: `{decision_sheet_path}`"
        if decision_sheet_path is not None
        else "- Decision sheet: not supplied"
    )
    return "\n".join(
        [
            "# Phase 1 Follow-Up Package",
            "",
            "This package turns an approved drop list into a ready-to-run follow-up plan.",
            "",
            "## Scope",
            f"- Source plan: `{source_plan_path}`",
            decision_line,
            f"- Dropped question count: `{len(dropped_question_ids)}`",
            "- Current package semantics: generate a fresh reduced-scope follow-up batch without mutating the already completed failed run.",
            "",
            "## Generated Files",
            f"- `followup_plan.json`: `{followup_plan_path}`",
            f"- `blocked_questions.json`: `{blocked_questions_path}`",
            f"- `calibration_manifest.json`: `{calibration_manifest_path}`",
            "- `lineage.json`: human-auditable link between the failed run and the prepared follow-up batch.",
            "",
            "## Execution",
            "Run the normal cohort entrypoint against the generated plan:",
            "",
            f"`python -m cps.runtime.cohort --plan {followup_plan_path} --backend live --env .env`",
            "",
            "## Reminder",
            "- This package prepares a future batch.",
            "- It does not clear the contamination gate for the source run.",
            "- It does not rewrite the original question text.",
            "- It keeps the replacement work in the sidecar / follow-up lane.",
        ]
    )


def build_followup_package(
    *,
    source_plan_path: str | Path,
    replacement_manifest_path: str | Path,
    output_root: str | Path,
    decision_sheet_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_source_plan_path = Path(source_plan_path).resolve()
    resolved_replacement_manifest_path = Path(replacement_manifest_path).resolve()
    resolved_output_root = Path(output_root).resolve()
    resolved_decision_sheet_path = (
        Path(decision_sheet_path).resolve() if decision_sheet_path is not None else None
    )

    source_plan = json.loads(resolved_source_plan_path.read_text(encoding="utf-8"))
    replacement_manifest = json.loads(
        resolved_replacement_manifest_path.read_text(encoding="utf-8")
    )
    bundle = load_manifest(
        _resolve_plan_path_value(
            source_plan,
            "manifest_path",
            plan_path=resolved_source_plan_path,
            root_dir=Path.cwd(),
        )
    )

    calibration_manifest_path = _resolve_plan_path_value(
        source_plan,
        "calibration_manifest_path",
        plan_path=resolved_source_plan_path,
        root_dir=Path.cwd(),
    )
    hash_path = _resolve_plan_path_value(
        source_plan,
        "hash_path",
        plan_path=resolved_source_plan_path,
        root_dir=Path.cwd(),
    )
    phase1_config_path = _resolve_plan_path_value(
        source_plan,
        "phase1_config_path",
        plan_path=resolved_source_plan_path,
        root_dir=Path.cwd(),
        default="phase1.yaml",
    )
    source_blocked_questions_path = _blocked_questions_path(calibration_manifest_path)
    existing_blocked_question_ids = _read_blocked_question_ids(source_blocked_questions_path)

    dropped_question_ids = sorted(
        {
            *existing_blocked_question_ids,
            *(str(question_id) for question_id in replacement_manifest.get("excluded_question_ids") or ()),
        }
    )
    seed = int(replacement_manifest["seed"])
    per_hop_count = int(source_plan["calibration"]["per_hop_count"])

    original_calibration = build_calibration_payload(
        bundle,
        seed=seed,
        per_hop_count=per_hop_count,
        exclude_question_ids=tuple(existing_blocked_question_ids),
    )
    followup_calibration = build_calibration_payload(
        bundle,
        seed=seed,
        per_hop_count=per_hop_count,
        exclude_question_ids=tuple(dropped_question_ids),
    )

    followup_storage = {
        "cache_dir": str((resolved_output_root / "cache").resolve()),
        "measurement_dir": str((resolved_output_root / "measurements").resolve()),
        "checkpoint_dir": str((resolved_output_root / "checkpoints").resolve()),
        "export_dir": str((resolved_output_root / "exports").resolve()),
    }
    ensure_directories(*(Path(path) for path in followup_storage.values()))

    followup_calibration_path = resolved_output_root / "calibration_manifest.json"
    followup_blocked_questions_path = resolved_output_root / "blocked_questions.json"
    followup_plan_path = resolved_output_root / "followup_plan.json"
    lineage_path = resolved_output_root / "lineage.json"
    readme_path = resolved_output_root / "README.md"

    write_json(followup_calibration_path, followup_calibration)
    write_json(
        followup_blocked_questions_path,
        {
            "blocked_question_ids": dropped_question_ids,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason_code": "approved_drop_list",
            "replacement_policy": "same_hop_next_rank_on_resume_v1",
            "source_plan_path": str(resolved_source_plan_path),
            "replacement_manifest_path": str(resolved_replacement_manifest_path),
        },
    )

    followup_plan = dict(source_plan)
    followup_plan["manifest_path"] = str(bundle.manifest_path)
    followup_plan["hash_path"] = str(hash_path)
    followup_plan["phase1_config_path"] = str(phase1_config_path)
    followup_plan["calibration_manifest_path"] = str(followup_calibration_path)
    followup_plan["storage"] = dict(followup_storage)
    followup_plan["generated_followup"] = {
        "package_version": FOLLOWUP_PACKAGE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_plan_path": str(resolved_source_plan_path),
        "replacement_manifest_path": str(resolved_replacement_manifest_path),
        "decision_sheet_path": (
            str(resolved_decision_sheet_path) if resolved_decision_sheet_path is not None else None
        ),
    }
    write_json(followup_plan_path, followup_plan)

    original_selected_ids = _selected_question_ids(original_calibration)
    followup_selected_ids = _selected_question_ids(followup_calibration)
    replacement_selected_ids = _selected_question_ids(replacement_manifest)
    new_selected_question_ids = [
        question_id for question_id in followup_selected_ids if question_id not in original_selected_ids
    ]
    removed_question_ids = [
        question_id for question_id in original_selected_ids if question_id not in followup_selected_ids
    ]
    alignment_status = (
        "matches_replacement_manifest"
        if followup_selected_ids == replacement_selected_ids
        else "differs_from_replacement_manifest"
    )
    lineage_payload = {
        "package_version": FOLLOWUP_PACKAGE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_plan_path": str(resolved_source_plan_path),
        "source_scope_mode": str(source_plan.get("scope_mode") or ""),
        "source_calibration_manifest_path": str(calibration_manifest_path),
        "source_blocked_questions_path": str(source_blocked_questions_path),
        "decision_sheet_path": (
            str(resolved_decision_sheet_path) if resolved_decision_sheet_path is not None else None
        ),
        "replacement_manifest_path": str(resolved_replacement_manifest_path),
        "seed": seed,
        "per_hop_count": per_hop_count,
        "preserved_blocked_question_ids": existing_blocked_question_ids,
        "dropped_question_ids": dropped_question_ids,
        "newly_added_drop_ids": [
            question_id
            for question_id in dropped_question_ids
            if question_id not in existing_blocked_question_ids
        ],
        "selection_alignment": {
            "status": alignment_status,
            "replacement_manifest_selected_question_ids": replacement_selected_ids,
            "generated_followup_selected_question_ids": followup_selected_ids,
        },
        "source_selected_by_hop": _selected_by_hop(original_calibration),
        "followup_selected_by_hop": _selected_by_hop(followup_calibration),
        "new_selected_question_ids": new_selected_question_ids,
        "removed_question_ids": removed_question_ids,
    }
    write_json(lineage_path, lineage_payload)
    write_text(
        readme_path,
        _followup_readme(
            source_plan_path=resolved_source_plan_path,
            decision_sheet_path=resolved_decision_sheet_path,
            dropped_question_ids=dropped_question_ids,
            followup_plan_path=followup_plan_path,
            blocked_questions_path=followup_blocked_questions_path,
            calibration_manifest_path=followup_calibration_path,
        ),
    )

    return {
        "status": "green",
        "package_version": FOLLOWUP_PACKAGE_VERSION,
        "output_root": str(resolved_output_root),
        "followup_plan_path": str(followup_plan_path),
        "calibration_manifest_path": str(followup_calibration_path),
        "blocked_questions_path": str(followup_blocked_questions_path),
        "lineage_path": str(lineage_path),
        "readme_path": str(readme_path),
        "dropped_question_ids": dropped_question_ids,
        "new_selected_question_ids": new_selected_question_ids,
        "selection_alignment": lineage_payload["selection_alignment"],
    }
