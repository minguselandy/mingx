import json
from pathlib import Path

import cps.runtime.followup as followup_module
from cps.data.manifest import load_manifest
from cps.runtime.calibration import build_calibration_manifest
from cps.runtime.followup import FOLLOWUP_PACKAGE_VERSION, build_followup_package


FIXTURE_MANIFEST = Path("artifacts/phase0/sample_manifest_v1.json")
FIXTURE_HASHES = Path("artifacts/phase0/content_hashes.json")


def _write_source_plan(path: Path, *, calibration_manifest_path: Path) -> None:
    payload = {
        "experiment_id": "musique_gate1_phase1_v1",
        "protocol_version": "phase1.v1",
        "phase1_config_path": str(Path("phase1.yaml").resolve()),
        "scope_mode": "pilot_reduced_scope",
        "manifest_path": str(FIXTURE_MANIFEST.resolve()),
        "hash_path": str(FIXTURE_HASHES.resolve()),
        "calibration_manifest_path": str(calibration_manifest_path.resolve()),
        "backend": "live",
        "question_paragraph_limit": 5,
        "calibration": {"per_hop_count": 1},
        "scoring": {"k_lcb": 5, "lcb_quantile": 0.1},
        "small_full_n": {"questions": "calibration_manifest"},
        "frontier_calibration": {"questions": "calibration_manifest"},
        "storage": {
            "cache_dir": str((path.parent / "source-cache").resolve()),
            "measurement_dir": str((path.parent / "source-measurements").resolve()),
            "checkpoint_dir": str((path.parent / "source-checkpoints").resolve()),
            "export_dir": str((path.parent / "source-exports").resolve()),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_source_run_summary(path: Path, *, run_id: str = "phase1-cohort-test-followup") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "backend": "live",
                "scope_mode": "pilot_reduced_scope",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_decision_sheet(
    path: Path,
    *,
    run_id: str,
    approved_followup_action: str,
    question_decisions: dict[str, str],
) -> None:
    rows = [
        f"| `{question_id}` | `drop_and_replace` | `{operator_decision}` | `signed_off` | ok | ok |"
        for question_id, operator_decision in question_decisions.items()
    ]
    path.write_text(
        "\n".join(
            [
                "# Contamination Operator Decision Sheet",
                "",
                f"- Run: `{run_id}`",
                "",
                "## Question Decisions",
                "",
                "| question_id | recommended action | operator decision | status | rationale | rerun precondition |",
                "| --- | --- | --- | --- | --- | --- |",
                *rows,
                "",
                "## Human Approval Block",
                "",
                "- Scientific owner: `owner-a`",
                "- Runtime owner: `owner-b`",
                "- Decision timestamp: `2026-04-23T12:00:00+08:00`",
                f"- Approved follow-up action: `{approved_followup_action}`",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_cli_inputs(
    workspace_tmp_dir: Path,
    *,
    approved_followup_action: str = "replace_only",
    question_decisions: dict[str, str] | None = None,
    decision_run_id: str = "phase1-cohort-test-followup",
) -> dict[str, Path]:
    bundle = load_manifest(FIXTURE_MANIFEST)
    dropped_question_ids = ("2hop__86458_20273",)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=dropped_question_ids,
    )
    _write_decision_sheet(
        decision_sheet_path,
        run_id=decision_run_id,
        approved_followup_action=approved_followup_action,
        question_decisions=question_decisions
        if question_decisions is not None
        else {"2hop__86458_20273": "drop_and_replace"},
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")

    return {
        "source_plan": source_plan_path,
        "replacement_manifest": replacement_manifest_path,
        "decision_sheet": decision_sheet_path,
        "output_root": workspace_tmp_dir / "followup-package",
    }


def test_followup_cli_builds_execution_ready_package_and_prints_output_paths(
    workspace_tmp_dir, capsys, monkeypatch
):
    import cps.runtime.cohort as cohort_module

    def fail_if_cohort_runs(*_args, **_kwargs):
        raise AssertionError("follow-up CLI must not run cohort execution")

    monkeypatch.setattr(cohort_module, "run_phase1_cohort", fail_if_cohort_runs)
    paths = _prepare_cli_inputs(workspace_tmp_dir)

    exit_code = followup_module.main(
        [
            "--source-plan",
            str(paths["source_plan"]),
            "--replacement-manifest",
            str(paths["replacement_manifest"]),
            "--decision-sheet",
            str(paths["decision_sheet"]),
            "--output-root",
            str(paths["output_root"]),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "green"
    assert payload["execution_ready"] is True
    assert payload["output_root"] == str(paths["output_root"].resolve())
    assert Path(payload["followup_plan_path"]).exists()
    assert Path(payload["calibration_manifest_path"]).exists()
    assert Path(payload["blocked_questions_path"]).exists()
    assert Path(payload["lineage_path"]).exists()
    assert Path(payload["readme_path"]).exists()
    assert "cps.runtime.cohort" not in captured.err


def test_followup_cli_returns_nonzero_for_missing_required_input(workspace_tmp_dir, capsys):
    paths = _prepare_cli_inputs(workspace_tmp_dir)

    exit_code = followup_module.main(
        [
            "--source-plan",
            str(paths["source_plan"]),
            "--replacement-manifest",
            str(paths["replacement_manifest"]),
            "--output-root",
            str(paths["output_root"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "--decision-sheet" in captured.err
    assert not paths["output_root"].exists()


def test_followup_cli_returns_nonzero_for_invalid_replacement_manifest(
    workspace_tmp_dir, capsys
):
    paths = _prepare_cli_inputs(workspace_tmp_dir)
    replacement_manifest = json.loads(
        paths["replacement_manifest"].read_text(encoding="utf-8")
    )
    replacement_manifest["seed"] = 123
    paths["replacement_manifest"].write_text(
        json.dumps(replacement_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    exit_code = followup_module.main(
        [
            "--source-plan",
            str(paths["source_plan"]),
            "--replacement-manifest",
            str(paths["replacement_manifest"]),
            "--decision-sheet",
            str(paths["decision_sheet"]),
            "--output-root",
            str(paths["output_root"]),
        ]
    )

    captured = capsys.readouterr()
    error_payload = json.loads(captured.err)
    assert exit_code != 0
    assert error_payload["status"] == "error"
    assert "seed does not match" in error_payload["error"]
    assert not paths["output_root"].exists()


def test_followup_cli_returns_nonzero_for_non_execution_ready_package(
    workspace_tmp_dir, capsys
):
    paths = _prepare_cli_inputs(
        workspace_tmp_dir,
        question_decisions={"2hop__86458_20273": "keep"},
    )

    exit_code = followup_module.main(
        [
            "--source-plan",
            str(paths["source_plan"]),
            "--replacement-manifest",
            str(paths["replacement_manifest"]),
            "--decision-sheet",
            str(paths["decision_sheet"]),
            "--output-root",
            str(paths["output_root"]),
        ]
    )

    captured = capsys.readouterr()
    output_payload = json.loads(captured.out)
    error_payload = json.loads(captured.err)
    assert exit_code != 0
    assert output_payload["execution_ready"] is False
    assert output_payload["approval_status"] == "question_decision_mismatch"
    assert error_payload["status"] == "not_execution_ready"
    assert error_payload["reason"] == "decision_sheet_question_decisions_do_not_match_drop_list"
    assert (paths["output_root"] / "followup_plan.json").exists()


def test_followup_package_builds_ready_to_run_plan_and_lineage(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    replacement_manifest = build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=(
            "2hop__86458_20273",
            "3hop1__222979_40769_64047",
            "4hop1__76111_624859_355213_203322",
        ),
    )
    _write_decision_sheet(
        decision_sheet_path,
        run_id="phase1-cohort-test-followup",
        approved_followup_action="replace_only",
        question_decisions={
            "2hop__86458_20273": "drop_and_replace",
            "3hop1__222979_40769_64047": "drop_and_replace",
            "4hop1__76111_624859_355213_203322": "drop_and_replace",
        },
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")

    output_root = workspace_tmp_dir / "followup-package"
    report = build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
        decision_sheet_path=decision_sheet_path,
    )

    followup_plan = json.loads((output_root / "followup_plan.json").read_text(encoding="utf-8"))
    blocked_questions = json.loads((output_root / "blocked_questions.json").read_text(encoding="utf-8"))
    followup_calibration = json.loads((output_root / "calibration_manifest.json").read_text(encoding="utf-8"))
    lineage = json.loads((output_root / "lineage.json").read_text(encoding="utf-8"))
    readme = (output_root / "README.md").read_text(encoding="utf-8")

    assert report["status"] == "green"
    assert report["package_version"] == FOLLOWUP_PACKAGE_VERSION
    assert Path(report["followup_plan_path"]).exists()
    assert Path(report["blocked_questions_path"]).exists()
    assert Path(report["calibration_manifest_path"]).exists()
    assert Path(report["lineage_path"]).exists()
    assert Path(report["readme_path"]).exists()
    assert followup_plan["generated_followup"]["package_version"] == FOLLOWUP_PACKAGE_VERSION
    assert followup_plan["calibration_manifest_path"] == str((output_root / "calibration_manifest.json").resolve())
    assert followup_plan["storage"]["export_dir"] == str((output_root / "exports").resolve())
    assert blocked_questions["blocked_question_ids"] == replacement_manifest["excluded_question_ids"]
    assert blocked_questions["replacement_policy"] == "same_hop_next_rank_on_resume_v1"
    assert _selected_question_ids(followup_calibration) == _selected_question_ids(replacement_manifest)
    assert report["approval"]["execution_ready"] is True
    assert report["approval"]["status"] == "approved_replace_only"
    assert lineage["selection_alignment"]["status"] == "matches_replacement_manifest"
    assert lineage["new_selected_question_ids"] == _selected_question_ids(replacement_manifest)
    assert lineage["source_run_id"] == "phase1-cohort-test-followup"
    assert Path(lineage["source_run_summary_path"]).exists()
    assert str(Path(lineage["source_events_path"]).name) == "events.jsonl"
    assert "python -m cps.runtime.cohort" in readme


def test_followup_package_merges_existing_blocked_ids_with_new_drop_list(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    (source_calibration_path.parent / "blocked_questions.json").write_text(
        json.dumps(
            {
                "blocked_question_ids": ["2hop__86458_20273"],
                "reason_code": "data_inspection_failed",
                "replacement_policy": "same_hop_next_rank_on_resume_v1",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=(
            "2hop__86458_20273",
            "3hop1__222979_40769_64047",
        ),
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")

    output_root = workspace_tmp_dir / "followup-package"
    build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
    )

    blocked_questions = json.loads((output_root / "blocked_questions.json").read_text(encoding="utf-8"))
    followup_calibration = json.loads((output_root / "calibration_manifest.json").read_text(encoding="utf-8"))
    lineage = json.loads((output_root / "lineage.json").read_text(encoding="utf-8"))

    assert blocked_questions["blocked_question_ids"] == [
        "2hop__86458_20273",
        "3hop1__222979_40769_64047",
    ]
    assert lineage["preserved_blocked_question_ids"] == ["2hop__86458_20273"]
    assert lineage["newly_added_drop_ids"] == ["3hop1__222979_40769_64047"]
    assert _selected_question_ids(followup_calibration) == [
        "2hop__132929_684936",
        "3hop1__409517_547811_80702",
        "4hop1__76111_624859_355213_203322",
    ]


def test_followup_package_rejects_output_root_inside_source_run_root(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )

    try:
        build_followup_package(
            source_plan_path=source_plan_path,
            replacement_manifest_path=replacement_manifest_path,
            output_root=source_calibration_path.parent,
        )
    except ValueError as exc:
        assert "output_root must not be the same as or nested under" in str(exc)
    else:
        raise AssertionError("expected output_root conflict to raise")


def test_followup_package_rejects_seed_mismatch_in_replacement_manifest(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    replacement_manifest = build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    replacement_manifest["seed"] = 123
    replacement_manifest_path.write_text(
        json.dumps(replacement_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    try:
        build_followup_package(
            source_plan_path=source_plan_path,
            replacement_manifest_path=replacement_manifest_path,
            output_root=workspace_tmp_dir / "followup-package",
        )
    except ValueError as exc:
        assert "seed does not match" in str(exc)
    else:
        raise AssertionError("expected replacement manifest seed mismatch to raise")
    assert not (workspace_tmp_dir / "followup-package" / "followup_plan.json").exists()


def test_followup_package_rejects_alignment_mismatch_without_creating_followup_tree(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    replacement_manifest = build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    replacement_manifest["selected_questions"][0]["question_id"] = "2hop__32254_84601"
    replacement_manifest_path.write_text(
        json.dumps(replacement_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_root = workspace_tmp_dir / "followup-package"
    try:
        build_followup_package(
            source_plan_path=source_plan_path,
            replacement_manifest_path=replacement_manifest_path,
            output_root=output_root,
        )
    except ValueError as exc:
        assert "does not match the supplied replacement manifest" in str(exc)
    else:
        raise AssertionError("expected alignment mismatch to raise")

    assert not output_root.exists()


def test_followup_package_marks_pending_decision_sheet_as_not_execution_ready(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    decision_sheet_path.write_text("Approved follow-up action: `[pending]`\n", encoding="utf-8")

    output_root = workspace_tmp_dir / "followup-package"
    report = build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
        decision_sheet_path=decision_sheet_path,
    )

    followup_plan = json.loads((output_root / "followup_plan.json").read_text(encoding="utf-8"))
    lineage = json.loads((output_root / "lineage.json").read_text(encoding="utf-8"))
    readme = (output_root / "README.md").read_text(encoding="utf-8")

    assert report["approval"]["status"] == "pending_human_signoff"
    assert report["approval"]["execution_ready"] is False
    assert followup_plan["generated_followup"]["decision_sheet_path"] == str(decision_sheet_path.resolve())
    assert lineage["approval"]["execution_ready"] is False
    assert "Execution ready: `False`" in readme


def test_followup_package_rejects_execution_ready_when_decision_sheet_run_id_mismatches(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")
    _write_decision_sheet(
        decision_sheet_path,
        run_id="phase1-cohort-other-run",
        approved_followup_action="replace_only",
        question_decisions={"2hop__86458_20273": "drop_and_replace"},
    )

    output_root = workspace_tmp_dir / "followup-package"
    report = build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
        decision_sheet_path=decision_sheet_path,
    )

    assert report["approval"]["status"] == "run_id_mismatch"
    assert report["approval"]["execution_ready"] is False


def test_followup_package_rejects_execution_ready_for_unsupported_followup_action(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=("2hop__86458_20273",),
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")
    _write_decision_sheet(
        decision_sheet_path,
        run_id="phase1-cohort-test-followup",
        approved_followup_action="return_to_phase0_revision",
        question_decisions={"2hop__86458_20273": "drop_and_replace"},
    )

    output_root = workspace_tmp_dir / "followup-package"
    report = build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
        decision_sheet_path=decision_sheet_path,
    )

    assert report["approval"]["status"] == "unsupported_followup_action"
    assert report["approval"]["execution_ready"] is False


def test_followup_package_rejects_execution_ready_when_question_decisions_do_not_match_drop_list(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    source_plan_path = workspace_tmp_dir / "source-plan.json"
    source_calibration_path = workspace_tmp_dir / "source-run" / "calibration_manifest.json"
    replacement_manifest_path = workspace_tmp_dir / "replacement_manifest.json"
    decision_sheet_path = workspace_tmp_dir / "decision-sheet.md"

    _write_source_plan(source_plan_path, calibration_manifest_path=source_calibration_path)
    build_calibration_manifest(
        bundle=bundle,
        output_path=source_calibration_path,
        seed=20260418,
        per_hop_count=1,
    )
    build_calibration_manifest(
        bundle=bundle,
        output_path=replacement_manifest_path,
        seed=20260418,
        per_hop_count=1,
        exclude_question_ids=(
            "2hop__86458_20273",
            "3hop1__222979_40769_64047",
        ),
    )
    _write_source_run_summary(workspace_tmp_dir / "source-exports" / "run_summary.json")
    _write_decision_sheet(
        decision_sheet_path,
        run_id="phase1-cohort-test-followup",
        approved_followup_action="replace_only",
        question_decisions={
            "2hop__86458_20273": "drop_and_replace",
            "3hop1__222979_40769_64047": "keep",
        },
    )

    output_root = workspace_tmp_dir / "followup-package"
    report = build_followup_package(
        source_plan_path=source_plan_path,
        replacement_manifest_path=replacement_manifest_path,
        output_root=output_root,
        decision_sheet_path=decision_sheet_path,
    )

    assert report["approval"]["status"] == "question_decision_mismatch"
    assert report["approval"]["execution_ready"] is False


def _selected_question_ids(payload: dict) -> list[str]:
    return [str(entry["question_id"]) for entry in payload["selected_questions"]]
