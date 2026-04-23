import json
from pathlib import Path

from cps.analysis.bridge import run_bridge_analysis


def _write_snapshot(
    measurement_dir: Path,
    *,
    model_role: str,
    question_id: str,
    hop_depth: str,
    values: dict[int, float],
    model_id: str,
) -> None:
    path = measurement_dir / "questions" / model_role / f"{question_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "question_id": question_id,
                "hop_depth": hop_depth,
                "V_model": model_id,
                "model_role": model_role,
                "baseline_logp": -2.0,
                "orderings": [],
                "delta_loo_LCB": [
                    {"paragraph_id": paragraph_id, "delta_loo": delta}
                    for paragraph_id, delta in sorted(values.items())
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_case(
    *,
    workspace_tmp_dir: Path,
    xs_by_hop: dict[str, list[float]],
    transform,
):
    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"

    selected_questions = []
    for hop_depth, xs in xs_by_hop.items():
        cal_question_id = f"{hop_depth}-cal"
        out_question_id = f"{hop_depth}-out"
        small_values = {index: value for index, value in enumerate(xs)}
        out_values = {index: value + 0.5 for index, value in enumerate(xs)}
        frontier_values = {index: float(transform(value)) for index, value in enumerate(xs)}
        _write_snapshot(
            measurement_dir,
            model_role="small",
            question_id=cal_question_id,
            hop_depth=hop_depth,
            values=small_values,
            model_id="qwen3-14b",
        )
        _write_snapshot(
            measurement_dir,
            model_role="small",
            question_id=out_question_id,
            hop_depth=hop_depth,
            values=out_values,
            model_id="qwen3-14b",
        )
        _write_snapshot(
            measurement_dir,
            model_role="frontier",
            question_id=cal_question_id,
            hop_depth=hop_depth,
            values=frontier_values,
            model_id="qwen3-32b",
        )
        selected_questions.append(
            {"question_id": cal_question_id, "hop_depth": hop_depth, "selection_score": hop_depth}
        )

    calibration_manifest_path.write_text(
        json.dumps(
            {
                "source_manifest_path": "synthetic",
                "source_manifest_hash": "synthetic-hash",
                "source_manifest_fingerprint": "sha256:synthetic",
                "seed": 20260418,
                "per_hop_counts": {hop_depth: 1 for hop_depth in xs_by_hop},
                "selection_algorithm_version": "synthetic-test",
                "selected_questions": selected_questions,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return measurement_dir, export_dir, calibration_manifest_path


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_jsonl(path: str | Path) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_run_bridge_analysis_keeps_linear_bridge_when_calibration_is_linear(workspace_tmp_dir):
    measurement_dir, export_dir, calibration_manifest_path = _write_case(
        workspace_tmp_dir=workspace_tmp_dir,
        xs_by_hop={
            "2hop": [1.0, 2.0, 3.0, 4.0, 5.0],
            "3hop": [1.5, 2.5, 3.5, 4.5, 5.5],
            "4hop": [2.0, 3.0, 4.0, 5.0, 6.0],
        },
        transform=lambda value: 1.0 + (2.0 * value),
    )

    report = run_bridge_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=20260418,
        bootstrap_resamples=40,
    )

    assert report["status"] == "computed"
    diagnostics = _load_json(report["bridge_diagnostics"])
    tolerance = _load_json(report["tolerance_band"])
    variance_budget = _load_json(report["variance_bias_budget"])
    bridged_rows = _load_jsonl(report["bridged_delta_loo_jsonl"])

    assert diagnostics["bridge_form"] == "linear_ols"
    assert diagnostics["pass_fail"] == "pass"
    assert diagnostics["recommended_next_action"] == "proceed_with_bridge_outputs"
    assert diagnostics["candidate_evaluations"][0]["bridge_form"] == "linear_ols"
    assert diagnostics["candidate_evaluations"][0]["pass_fail"] == "pass"
    for hop_depth in ("2hop", "3hop", "4hop"):
        coefficients = diagnostics["per_hop"][hop_depth]["coefficients"]
        assert round(coefficients["intercept"], 6) == 1.0
        assert round(coefficients["slope"], 6) == 2.0
        assert diagnostics["per_hop"][hop_depth]["pass_flags"]["diagnostic_triplet_pass"] is True
    assert diagnostics["pooled_overlap"]["pearson_pass"] is True
    assert diagnostics["pooled_overlap"]["mae_pass"] is True
    assert tolerance["status"] == "computed"
    assert variance_budget["status"] == "computed"
    assert variance_budget["bridge_status"] == "computed"
    assert variance_budget["bridge_form"] == "linear_ols"
    assert variance_budget["pass_fail"] == "pass"
    assert variance_budget["escalation_reason"] == "linear_ols satisfied the bridge pass criteria"
    assert variance_budget["recommended_next_action"] == "proceed_with_bridge_outputs"
    assert variance_budget["per_hop"]["2hop"]["bridge_coefficient_variance"]["intercept"] >= 0.0

    out_sample = next(
        row for row in bridged_rows if row["question_id"] == "2hop-out" and row["paragraph_id"] == 0
    )
    assert out_sample["bridge_form"] == "linear_ols"
    assert out_sample["bridge_source"] == "bridged_small"
    assert round(out_sample["delta_loo_frontier_equivalent"], 6) == 4.0


def test_run_bridge_analysis_escalates_to_isotonic_for_monotonic_step_shape(workspace_tmp_dir):
    measurement_dir, export_dir, calibration_manifest_path = _write_case(
        workspace_tmp_dir=workspace_tmp_dir,
        xs_by_hop={
            "2hop": [0.0, 1.0, 2.0, 3.0, 4.0],
            "3hop": [0.0, 1.0, 2.0, 3.0, 4.0],
            "4hop": [0.0, 1.0, 2.0, 3.0, 4.0],
        },
        transform=lambda value: 0.0 if value < 2.5 else 10.0,
    )

    report = run_bridge_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=20260418,
        bootstrap_resamples=40,
    )

    diagnostics = _load_json(report["bridge_diagnostics"])
    assert report["status"] == "computed"
    assert diagnostics["bridge_form"] == "isotonic"
    assert diagnostics["selected_candidate_form"] == "isotonic"
    assert diagnostics["pass_fail"] == "pass"
    assert diagnostics["candidate_evaluations"][0]["bridge_form"] == "linear_ols"
    assert diagnostics["candidate_evaluations"][0]["pass_fail"] == "fail"
    assert diagnostics["candidate_evaluations"][1]["bridge_form"] == "isotonic"
    assert diagnostics["candidate_evaluations"][1]["pass_fail"] == "pass"
    assert "breakpoints_x" in diagnostics["per_hop"]["2hop"]["coefficients"]


def test_run_bridge_analysis_escalates_to_quadratic_for_non_monotonic_curve(workspace_tmp_dir):
    measurement_dir, export_dir, calibration_manifest_path = _write_case(
        workspace_tmp_dir=workspace_tmp_dir,
        xs_by_hop={
            "2hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
            "3hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
            "4hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
        },
        transform=lambda value: 4.0 - (value * value),
    )

    report = run_bridge_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=20260418,
        bootstrap_resamples=40,
    )

    diagnostics = _load_json(report["bridge_diagnostics"])
    bridged_rows = _load_jsonl(report["bridged_delta_loo_jsonl"])

    assert report["status"] == "computed"
    assert diagnostics["bridge_form"] == "polynomial_quadratic"
    assert diagnostics["candidate_evaluations"][0]["pass_fail"] == "fail"
    assert diagnostics["candidate_evaluations"][1]["pass_fail"] == "fail"
    assert diagnostics["candidate_evaluations"][2]["pass_fail"] == "pass"
    coefficients = diagnostics["per_hop"]["2hop"]["coefficients"]
    assert round(coefficients["quadratic"], 6) == -1.0
    assert round(coefficients["intercept"], 6) == 4.0
    sample = next(row for row in bridged_rows if row["question_id"] == "2hop-out" and row["paragraph_id"] == 0)
    assert sample["bridge_form"] == "polynomial_quadratic"


def test_run_bridge_analysis_reports_frontier_full_n_when_all_bridge_forms_fail(workspace_tmp_dir):
    transform_map = {
        -2.0: 0.0,
        -1.0: 2.0,
        0.0: 0.0,
        1.0: 2.0,
        2.0: 0.0,
    }
    measurement_dir, export_dir, calibration_manifest_path = _write_case(
        workspace_tmp_dir=workspace_tmp_dir,
        xs_by_hop={
            "2hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
            "3hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
            "4hop": [-2.0, -1.0, 0.0, 1.0, 2.0],
        },
        transform=lambda value: transform_map[float(value)],
    )

    report = run_bridge_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=20260418,
        bootstrap_resamples=40,
    )

    diagnostics = _load_json(report["bridge_diagnostics"])
    variance_budget = _load_json(report["variance_bias_budget"])
    tolerance = _load_json(report["tolerance_band"])

    assert report["status"] == "frontier_full_n_required"
    assert diagnostics["status"] == "frontier_full_n_required"
    assert diagnostics["bridge_form"] == "frontier_full_n_required"
    assert diagnostics["selected_candidate_form"] == "polynomial_quadratic"
    assert diagnostics["pass_fail"] == "fail"
    assert diagnostics["recommended_next_action"] == "execute_v_frontier_on_full_n"
    assert variance_budget["bridge_status"] == "frontier_full_n_required"
    assert variance_budget["bridge_form"] == "frontier_full_n_required"
    assert variance_budget["pass_fail"] == "fail"
    assert variance_budget["recommended_next_action"] == "execute_v_frontier_on_full_n"
    assert "All configured bridge forms failed pass criteria" in variance_budget["escalation_reason"]
    assert tolerance["status"] == "provisional_bridge_only"
    assert Path(report["bridged_delta_loo_jsonl"]).exists()
