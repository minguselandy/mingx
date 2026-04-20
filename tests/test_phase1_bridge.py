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


def test_run_bridge_analysis_computes_coefficients_and_tolerance_band(workspace_tmp_dir):
    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"

    questions = {
        "2hop-cal": ("2hop", {0: 1.0, 1: 2.0}),
        "2hop-out": ("2hop", {0: 3.0, 1: 4.0}),
        "3hop-cal": ("3hop", {0: 1.5, 1: 2.5}),
        "3hop-out": ("3hop", {0: 3.5, 1: 4.5}),
        "4hop-cal": ("4hop", {0: 2.0, 1: 3.0}),
        "4hop-out": ("4hop", {0: 4.0, 1: 5.0}),
    }

    for question_id, (hop_depth, values) in questions.items():
        _write_snapshot(
            measurement_dir,
            model_role="small",
            question_id=question_id,
            hop_depth=hop_depth,
            values=values,
            model_id="qwen3-14b",
        )

    for question_id, (hop_depth, values) in questions.items():
        if not question_id.endswith("-cal"):
            continue
        _write_snapshot(
            measurement_dir,
            model_role="frontier",
            question_id=question_id,
            hop_depth=hop_depth,
            values={paragraph_id: 1.0 + (2.0 * value) for paragraph_id, value in values.items()},
            model_id="qwen3-32b",
        )

    calibration_manifest_path.write_text(
        json.dumps(
            {
                "source_manifest_path": "synthetic",
                "source_manifest_hash": "synthetic-hash",
                "source_manifest_fingerprint": "sha256:synthetic",
                "seed": 20260418,
                "per_hop_counts": {"2hop": 1, "3hop": 1, "4hop": 1},
                "selection_algorithm_version": "synthetic-test",
                "selected_questions": [
                    {"question_id": "2hop-cal", "hop_depth": "2hop", "selection_score": "a"},
                    {"question_id": "3hop-cal", "hop_depth": "3hop", "selection_score": "b"},
                    {"question_id": "4hop-cal", "hop_depth": "4hop", "selection_score": "c"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = run_bridge_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=20260418,
        bootstrap_resamples=40,
    )

    assert report["status"] == "computed"
    assert Path(report["bridge_diagnostics"]).exists()
    assert Path(report["bridged_delta_loo_jsonl"]).exists()
    assert Path(report["tolerance_band"]).exists()
    assert Path(report["variance_bias_budget"]).exists()

    diagnostics = json.loads(Path(report["bridge_diagnostics"]).read_text(encoding="utf-8"))
    for hop_depth in ("2hop", "3hop", "4hop"):
        coefficients = diagnostics["per_hop"][hop_depth]["coefficients"]
        assert round(coefficients["intercept"], 6) == 1.0
        assert round(coefficients["slope"], 6) == 2.0
        assert diagnostics["per_hop"][hop_depth]["consistency"]["pearson_r"] == 1.0
        assert diagnostics["per_hop"][hop_depth]["diagnostics"]["normality_test"] == "shapiro_wilk"

    bridged_rows = [
        json.loads(line)
        for line in Path(report["bridged_delta_loo_jsonl"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(bridged_rows) == 12
    out_sample = next(
        row for row in bridged_rows if row["question_id"] == "2hop-out" and row["paragraph_id"] == 0
    )
    assert out_sample["bridge_source"] == "bridged_small"
    assert out_sample["delta_loo_frontier_equivalent"] == 7.0

    tolerance = json.loads(Path(report["tolerance_band"]).read_text(encoding="utf-8"))
    assert tolerance["status"] == "computed"
    assert tolerance["per_hop"]["2hop"]["counts"]["total"] == 4
    assert "lower_cut" in tolerance["per_hop"]["2hop"]

    variance_budget = json.loads(Path(report["variance_bias_budget"]).read_text(encoding="utf-8"))
    assert variance_budget["status"] == "computed"
    assert variance_budget["per_hop"]["2hop"]["bridge_coefficient_variance"]["intercept"] >= 0.0
