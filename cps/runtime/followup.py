from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cps.analysis.exports import ensure_directories, write_json, write_text
from cps.data.manifest import load_manifest
from cps.runtime.calibration import SELECTION_ALGORITHM_VERSION, build_calibration_payload
from cps.runtime.cohort import _blocked_questions_path, _read_blocked_question_ids
from cps.store.measurement import events_path_for


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


def _is_same_or_within(path: Path, protected_root: Path) -> bool:
    resolved_path = path.resolve()
    resolved_root = protected_root.resolve()
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def _load_json(path: Path, *, required: bool) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise ValueError(f"required artifact is missing: {path}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_decision_sheet(decision_sheet_path: Path) -> dict[str, Any]:
    content = decision_sheet_path.read_text(encoding="utf-8")
    run_match = re.search(r"^- Run:\s*`([^`]+)`", content, flags=re.MULTILINE)
    action_match = re.search(
        r"^- Approved follow-up action:\s*`([^`]+)`", content, flags=re.MULTILINE
    )
    decisions: dict[str, str] = {}
    for match in re.finditer(
        r"^\|\s*`([^`]+)`\s*\|\s*`[^`]+`\s*\|\s*`([^`]+)`\s*\|",
        content,
        flags=re.MULTILINE,
    ):
        question_id, operator_decision = match.groups()
        decisions[str(question_id)] = str(operator_decision)
    return {
        "raw_text": content,
        "run_id": str(run_match.group(1)) if run_match else "",
        "approved_followup_action": str(action_match.group(1)) if action_match else "",
        "question_decisions": decisions,
    }


def _decision_approval_state(
    decision_sheet_path: Path | None,
    *,
    source_run_id: str,
    dropped_question_ids: list[str],
) -> dict[str, Any]:
    if decision_sheet_path is None:
        return {
            "status": "not_provided",
            "execution_ready": False,
            "reason": "decision_sheet_not_supplied",
        }
    parsed = _parse_decision_sheet(decision_sheet_path)
    content = parsed["raw_text"]
    if "[pending]" in content:
        return {
            "status": "pending_human_signoff",
            "execution_ready": False,
            "reason": "decision_sheet_contains_pending_placeholders",
        }
    if not parsed["run_id"]:
        return {
            "status": "missing_run_id",
            "execution_ready": False,
            "reason": "decision_sheet_missing_run_id",
        }
    if parsed["run_id"] != str(source_run_id):
        return {
            "status": "run_id_mismatch",
            "execution_ready": False,
            "reason": "decision_sheet_run_id_mismatch",
            "decision_sheet_run_id": parsed["run_id"],
            "source_run_id": str(source_run_id),
        }
    if not parsed["approved_followup_action"]:
        return {
            "status": "missing_approved_followup_action",
            "execution_ready": False,
            "reason": "decision_sheet_missing_approved_followup_action",
        }
    if parsed["approved_followup_action"] != "replace_only":
        return {
            "status": "unsupported_followup_action",
            "execution_ready": False,
            "reason": "decision_sheet_approved_followup_action_not_supported_by_this_helper",
            "approved_followup_action": parsed["approved_followup_action"],
        }
    missing_question_ids = [
        question_id
        for question_id in dropped_question_ids
        if parsed["question_decisions"].get(question_id) != "drop_and_replace"
    ]
    if missing_question_ids:
        return {
            "status": "question_decision_mismatch",
            "execution_ready": False,
            "reason": "decision_sheet_question_decisions_do_not_match_drop_list",
            "question_ids": missing_question_ids,
        }
    return {
        "status": "approved_replace_only",
        "execution_ready": True,
        "reason": "decision_sheet_matches_replace_only_followup",
        "approved_followup_action": parsed["approved_followup_action"],
    }


def _validate_output_root(
    *,
    output_root: Path,
    source_calibration_manifest_path: Path,
    source_storage_paths: dict[str, Path],
) -> None:
    protected_roots = {
        "source_run_root": source_calibration_manifest_path.parent.resolve(),
        "source_export_dir": source_storage_paths["export_dir"].resolve(),
        "source_measurement_dir": source_storage_paths["measurement_dir"].resolve(),
        "source_checkpoint_dir": source_storage_paths["checkpoint_dir"].resolve(),
        "source_cache_dir": source_storage_paths["cache_dir"].resolve(),
    }
    for label, protected_root in protected_roots.items():
        if _is_same_or_within(output_root, protected_root):
            raise ValueError(
                f"output_root must not be the same as or nested under {label}: {protected_root}"
            )


def _validate_replacement_manifest(
    *,
    replacement_manifest: dict[str, Any],
    source_calibration: dict[str, Any],
    bundle,
    per_hop_count: int,
) -> None:
    expected_dataset_hash = bundle.source_dataset.get("content_hash_sha256")
    if str(replacement_manifest.get("source_manifest_hash") or "") != str(bundle.manifest_hash):
        raise ValueError("replacement manifest source_manifest_hash does not match source manifest")
    if str(replacement_manifest.get("source_dataset_hash") or "") != str(expected_dataset_hash):
        raise ValueError("replacement manifest source_dataset_hash does not match source dataset")
    if int(replacement_manifest.get("seed", -1)) != int(source_calibration.get("seed", -1)):
        raise ValueError("replacement manifest seed does not match source calibration manifest")
    if (
        str(replacement_manifest.get("selection_algorithm_version") or "")
        != SELECTION_ALGORITHM_VERSION
    ):
        raise ValueError("replacement manifest selection_algorithm_version is not supported")
    if (
        str(replacement_manifest.get("selection_algorithm_version") or "")
        != str(source_calibration.get("selection_algorithm_version") or "")
    ):
        raise ValueError(
            "replacement manifest selection_algorithm_version does not match source calibration manifest"
        )
    if str(replacement_manifest.get("replacement_policy") or "") != "same_hop_next_rank_on_resume_v1":
        raise ValueError("replacement manifest replacement_policy is not supported")
    expected_per_hop_counts = {
        hop_depth: per_hop_count
        for hop_depth in sorted({question.hop_depth for question in bundle.sample})
    }
    actual_per_hop_counts = {
        str(hop_depth): int(count)
        for hop_depth, count in dict(replacement_manifest.get("per_hop_counts") or {}).items()
    }
    if actual_per_hop_counts != expected_per_hop_counts:
        raise ValueError("replacement manifest per_hop_counts do not match the source plan")


def _followup_readme(
    *,
    source_plan_path: Path,
    decision_sheet_path: Path | None,
    dropped_question_ids: list[str],
    followup_plan_path: Path,
    blocked_questions_path: Path,
    calibration_manifest_path: Path,
    approval_state: dict[str, Any],
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
            "This package turns an approved drop list into a prepared follow-up plan.",
            "",
            "## Scope",
            f"- Source plan: `{source_plan_path}`",
            decision_line,
            f"- Dropped question count: `{len(dropped_question_ids)}`",
            f"- Approval status: `{approval_state['status']}`",
            f"- Execution ready: `{approval_state['execution_ready']}`",
            "- Current package semantics: generate a fresh reduced-scope follow-up batch without mutating the already completed failed run.",
            "",
            "## Generated Files",
            f"- `followup_plan.json`: `{followup_plan_path}`",
            f"- `blocked_questions.json`: `{blocked_questions_path}`",
            f"- `calibration_manifest.json`: `{calibration_manifest_path}`",
            "- `lineage.json`: human-auditable link between the failed run and the prepared follow-up batch.",
            "",
            "## Execution",
            "Run the normal cohort entrypoint against the generated plan only after the decision sheet is approved and execution-ready:",
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
    source_storage_paths = {
        key: _resolve_plan_path_value(
            dict(source_plan["storage"]),
            key,
            plan_path=resolved_source_plan_path,
            root_dir=Path.cwd(),
        )
        for key in ("cache_dir", "measurement_dir", "checkpoint_dir", "export_dir")
    }
    _validate_output_root(
        output_root=resolved_output_root,
        source_calibration_manifest_path=calibration_manifest_path,
        source_storage_paths=source_storage_paths,
    )

    source_blocked_questions_path = _blocked_questions_path(calibration_manifest_path)
    existing_blocked_question_ids = _read_blocked_question_ids(source_blocked_questions_path)
    source_calibration = _load_json(calibration_manifest_path, required=True)

    dropped_question_ids = sorted(
        {
            *existing_blocked_question_ids,
            *(str(question_id) for question_id in replacement_manifest.get("excluded_question_ids") or ()),
        }
    )
    seed = int(replacement_manifest["seed"])
    per_hop_count = int(source_plan["calibration"]["per_hop_count"])
    _validate_replacement_manifest(
        replacement_manifest=replacement_manifest,
        source_calibration=source_calibration,
        bundle=bundle,
        per_hop_count=per_hop_count,
    )

    original_calibration = dict(source_calibration)
    followup_calibration = build_calibration_payload(
        bundle,
        seed=seed,
        per_hop_count=per_hop_count,
        exclude_question_ids=tuple(dropped_question_ids),
    )

    followup_calibration_path = resolved_output_root / "calibration_manifest.json"
    followup_blocked_questions_path = resolved_output_root / "blocked_questions.json"
    followup_plan_path = resolved_output_root / "followup_plan.json"
    lineage_path = resolved_output_root / "lineage.json"
    readme_path = resolved_output_root / "README.md"

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
    if alignment_status != "matches_replacement_manifest":
        raise ValueError(
            "generated follow-up calibration does not match the supplied replacement manifest"
        )
    followup_storage = {
        "cache_dir": str((resolved_output_root / "cache").resolve()),
        "measurement_dir": str((resolved_output_root / "measurements").resolve()),
        "checkpoint_dir": str((resolved_output_root / "checkpoints").resolve()),
        "export_dir": str((resolved_output_root / "exports").resolve()),
    }
    ensure_directories(*(Path(path) for path in followup_storage.values()))
    source_run_summary_path = source_storage_paths["export_dir"] / "run_summary.json"
    source_run_summary = _load_json(source_run_summary_path, required=False) or {}
    source_events_path = events_path_for(source_storage_paths["measurement_dir"])
    approval_state = _decision_approval_state(
        resolved_decision_sheet_path,
        source_run_id=str(source_run_summary.get("run_id") or ""),
        dropped_question_ids=dropped_question_ids,
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
        "approval": dict(approval_state),
    }
    lineage_payload = {
        "package_version": FOLLOWUP_PACKAGE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_plan_path": str(resolved_source_plan_path),
        "source_run_id": str(source_run_summary.get("run_id") or ""),
        "source_scope_mode": str(source_plan.get("scope_mode") or ""),
        "source_calibration_manifest_path": str(calibration_manifest_path),
        "source_blocked_questions_path": str(source_blocked_questions_path),
        "source_run_summary_path": str(source_run_summary_path),
        "source_events_path": str(source_events_path),
        "decision_sheet_path": (
            str(resolved_decision_sheet_path) if resolved_decision_sheet_path is not None else None
        ),
        "approval": approval_state,
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
    write_json(followup_plan_path, followup_plan)
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
            approval_state=approval_state,
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
        "approval": approval_state,
        "selection_alignment": lineage_payload["selection_alignment"],
    }
