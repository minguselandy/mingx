import json
from pathlib import Path

import cps.runtime.cohort as phase1_run_module
from cps.analysis.contamination import CONTAMINATION_THRESHOLD_LOGP
from cps.data.manifest import load_manifest
from cps.scoring.backends import MockScoringBackend, ScoreResult
from cps.scoring.orderings import build_orderings
from cps.runtime.cohort import run_phase1_cohort
from cps.store.measurement import append_event, iter_events
from tests.helpers_phase1 import complete_annotation_labels, complete_annotation_labels_as_human


def _write_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-test-key",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )


def _write_plan(path: Path, *, measurement_dir: Path, export_dir: Path, checkpoint_dir: Path, cache_dir: Path, calibration_manifest_path: Path, small_questions, frontier_questions) -> None:
    payload = {
        "experiment_id": "musique_gate1_phase1_v1",
        "protocol_version": "phase1.v1",
        "phase1_config_path": "./phase1.yaml",
        "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
        "hash_path": "./artifacts/phase0/content_hashes.json",
        "calibration_manifest_path": str(calibration_manifest_path.as_posix()),
        "backend": "mock",
        "scoring": {
            "k_lcb": 5,
            "lcb_quantile": 0.1,
        },
        "small_full_n": {
            "questions": small_questions,
        },
        "frontier_calibration": {
            "questions": frontier_questions,
        },
        "storage": {
            "measurement_dir": str(measurement_dir.as_posix()),
            "export_dir": str(export_dir.as_posix()),
            "checkpoint_dir": str(checkpoint_dir.as_posix()),
            "cache_dir": str(cache_dir.as_posix()),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_phase1_cohort_runner_rebuilds_missing_derivations_without_rescoring(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = bundle.sample[0]
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    plan_path = workspace_tmp_dir / "cohort_plan.json"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions=[question.question_id],
        frontier_questions=[],
    )

    orderings = build_orderings(
        question.question_id,
        [paragraph.paragraph_id for paragraph in question.paragraphs],
        k_lcb=5,
        canonical_ordering_id="canonical_v1",
        seed=20260418,
    )
    shared = {
        "run_id": "preexisting-run",
        "question_id": question.question_id,
        "hop_depth": question.hop_depth,
        "provider": "dashscope",
        "backend_id": "mock_forced_decode",
        "model_id": "qwen3-14b",
        "model_role": "small",
        "manifest_hash": bundle.manifest_hash,
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "request_fingerprint": "fp",
        "response_status": "mock",
        "notes": "fixture",
        "payload": {},
    }

    append_event(
        measurement_dir,
        {
            "event_type": "baseline_scored",
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.5,
            **shared,
        },
    )
    for ordering in orderings:
        append_event(
            measurement_dir,
            {
                "event_type": "full_scored",
                "ordering_id": ordering.ordering_id,
                "ordering": list(ordering.paragraph_ids),
                "paragraph_id": None,
                "full_logp": -1.2,
                "loo_logp": None,
                "delta_loo": None,
                "baseline_logp": -2.5,
                **shared,
            },
        )
        for paragraph_id in ordering.paragraph_ids:
            append_event(
                measurement_dir,
                {
                    "event_type": "loo_scored",
                    "ordering_id": ordering.ordering_id,
                    "ordering": list(ordering.paragraph_ids),
                    "paragraph_id": paragraph_id,
                    "full_logp": -1.2,
                    "loo_logp": -1.4,
                    "delta_loo": 0.2,
                    "baseline_logp": -2.5,
                    **shared,
                },
            )
            append_event(
                measurement_dir,
                {
                    "event_type": "ordering_scored",
                    "ordering_id": ordering.ordering_id,
                    "ordering": list(ordering.paragraph_ids),
                    "paragraph_id": paragraph_id,
                    "full_logp": -1.2,
                    "loo_logp": -1.4,
                    "delta_loo": 0.2,
                    "baseline_logp": -2.5,
                    **shared,
                },
            )

    before_baselines = [
        event
        for event in iter_events(measurement_dir)
        if event["event_type"] == "baseline_scored" and event.get("model_role") == "small"
    ]

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    after_baselines = [
        event
        for event in iter_events(measurement_dir)
        if event["event_type"] == "baseline_scored" and event.get("model_role") == "small"
    ]

    assert report["status"] == "red"
    assert len(before_baselines) == 1
    assert len(after_baselines) == 1
    assert Path(report["calibration_manifest_path"]).exists()
    assert Path(report["run_summary_path"]).exists()
    assert Path(export_dir / "small" / "questions" / question.question_id / "export_manifest.json").exists()
    assert Path(measurement_dir / "questions" / "small" / f"{question.question_id}.json").exists()
    assert report["summary"]["model_roles"]["small"]["completed"] == 1
    assert report["summary"]["model_roles"]["small"]["incomplete"] == 0


def test_phase1_cohort_runner_ignores_checkpoint_if_event_log_is_incomplete(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    by_hop = {}
    for question in bundle.sample:
        by_hop.setdefault(question.hop_depth, question.question_id)
    small_question_ids = [by_hop["2hop"], by_hop["3hop"], by_hop["4hop"]]
    frontier_question_ids = [by_hop["2hop"]]

    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_plan.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["calibration"] = {"per_hop_count": 1}
    payload["question_paragraph_limit"] = 5
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "bogus.json").write_text(
        json.dumps(
            {
                "source_of_truth": "event_log",
                "progress": {
                    "small": {"completed": small_question_ids},
                    "frontier": {"completed": frontier_question_ids},
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    assert first_report["status"] == "awaiting_annotation"
    assert first_report["summary"]["pipeline_status"] == "awaiting_annotation"
    assert first_report["summary"]["measurement_status"] == "pilot_only"
    complete_annotation_labels(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert report["summary"]["annotation_mode"] == "synthetic_passthrough"
    assert Path(report["calibration_manifest_path"]).exists()
    assert report["summary"]["model_roles"]["small"]["planned"] == 3
    assert report["summary"]["model_roles"]["small"]["completed"] == 3
    assert first_report["summary"]["model_roles"]["small"]["skipped"] == 0


def test_phase1_cohort_runner_marks_protocol_full_human_labels_as_measurement_validated(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_protocol_full_human.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["scope_mode"] = "protocol_full"
    payload["calibration"] = {"per_hop_count": 1}
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert first_report["status"] == "awaiting_annotation"
    assert first_report["summary"]["measurement_status"] == "awaiting_real_annotation"
    complete_annotation_labels_as_human(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["scope_mode"] == "protocol_full"
    assert report["summary"]["annotation_mode"] == "human_labels"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["measurement_status"] == "measurement_validated"
    assert report["summary"]["contamination"]["gate_decision"] == "pass"
    assert Path(report["summary"]["training_manifest_path"]).exists()
    assert Path(report["summary"]["kappa"]["kappa_summary_path"]).exists()
    assert Path(report["training_manifest_path"]).exists()
    calibration_manifest = json.loads(calibration_manifest_path.read_text(encoding="utf-8"))
    lookup = {question.question_id: question for question in load_manifest("artifacts/phase0/sample_manifest_v1.json").sample}
    selected_question_ids = [entry["question_id"] for entry in calibration_manifest["selected_questions"]]
    per_role_equivalent = sum((lookup[question_id].paragraph_count + 1) * 5 for question_id in selected_question_ids)
    budget = report["summary"]["budget"]
    assert budget["current_plan"]["equivalent_forward_passes"] == {
        "small": per_role_equivalent,
        "frontier": per_role_equivalent,
        "total": per_role_equivalent * 2,
    }
    assert budget["current_plan"]["runner_api_calls"]["total"] == (per_role_equivalent * 2) + 6
    assert budget["reference_phase1_probe_budget"]["status"] == "not_applicable"
    assert Path(report["summary"]["contamination"]["escalation_bundle_path"]).exists()


def test_phase1_cohort_runner_keeps_protocol_full_synthetic_path_at_pilot_only(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_protocol_full_synthetic.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["scope_mode"] = "protocol_full"
    payload["calibration"] = {"per_hop_count": 1}
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    complete_annotation_labels(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["scope_mode"] == "protocol_full"
    assert report["summary"]["annotation_mode"] == "synthetic_passthrough"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert Path(report["summary"]["training_manifest_path"]).exists()
    assert Path(report["summary"]["contamination"]["escalation_bundle_path"]).exists()
    assert report["summary"]["model_roles"]["small"]["skipped"] == 3
    assert report["summary"]["model_roles"]["frontier"]["planned"] == 3
    assert report["summary"]["model_roles"]["frontier"]["completed"] == 3
    assert report["summary"]["question_counts"]["small"] == {
        "planned": 3,
        "completed": 3,
        "skipped": 3,
        "remaining": 0,
    }
    assert report["summary"]["question_counts"]["frontier"] == {
        "planned": 3,
        "completed": 3,
        "skipped": 3,
        "remaining": 0,
    }
    calibration_manifest = json.loads(calibration_manifest_path.read_text(encoding="utf-8"))
    selected_question_ids = [entry["question_id"] for entry in calibration_manifest["selected_questions"]]
    assert Path(export_dir / "small" / "questions" / selected_question_ids[0] / "export_manifest.json").exists()
    assert Path(export_dir / "frontier" / "questions" / selected_question_ids[0] / "export_manifest.json").exists()


def test_phase1_cohort_runner_stops_measurement_validation_when_contamination_gate_fails(
    workspace_tmp_dir, monkeypatch
):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_protocol_full_contamination_fail.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["scope_mode"] = "protocol_full"
    payload["calibration"] = {"per_hop_count": 1}
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    class ContaminatedFrontierBackend(MockScoringBackend):
        def score_answer(self, question_text, answer_text, ordered_paragraphs):
            result = super().score_answer(question_text, answer_text, ordered_paragraphs)
            if not ordered_paragraphs and self.model_id == "qwen3-32b":
                return ScoreResult(
                    logprob_sum=CONTAMINATION_THRESHOLD_LOGP + 0.5,
                    raw_content=result.raw_content,
                    request_fingerprint=result.request_fingerprint,
                    response_status=result.response_status,
                    token_logprobs=result.token_logprobs,
                    metadata=result.metadata,
                )
            return result

    def _fake_build_backend(context, backend_name, model_role):
        model_id = "qwen3-32b" if model_role == "frontier" else "qwen3-14b"
        return ContaminatedFrontierBackend(model_id=model_id)

    monkeypatch.setattr(phase1_run_module, "_build_backend", _fake_build_backend)

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert first_report["status"] == "awaiting_annotation"
    assert first_report["summary"]["contamination"]["gate_decision"] == "fail"
    assert first_report["summary"]["measurement_status"] == "awaiting_contamination_check"

    complete_annotation_labels_as_human(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["annotation_mode"] == "human_labels"
    assert report["summary"]["contamination"]["gate_decision"] == "fail"
    assert report["summary"]["measurement_status"] == "awaiting_contamination_check"
    assert Path(report["summary"]["kappa"]["kappa_summary_path"]).exists()
    bundle_path = Path(report["summary"]["contamination"]["escalation_bundle_path"])
    assert bundle_path.exists()
    contamination_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert contamination_bundle["status"] == "manual_decision_required"
    assert contamination_bundle["default_operator_action"] == "stop_and_escalate"
    assert contamination_bundle["automation_policy"]["auto_restrict_to_uncontaminated_subset"] is False
    assert contamination_bundle["automation_policy"]["auto_rerun_protocol_full"] is False
    assert contamination_bundle["automation_policy"]["auto_upgrade_to_measurement_validated"] is False
    assert contamination_bundle["artifact_paths"]["run_summary"] == report["run_summary_path"]
    assert contamination_bundle["recommended_actions"][0]["selected_by_default"] is False


def test_phase1_cohort_runner_supports_optional_paragraph_limit(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = bundle.sample[0]

    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_plan.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions=[question.question_id],
        frontier_questions=[],
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["question_paragraph_limit"] = 5
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    snapshot = json.loads(
        (measurement_dir / "questions" / "small" / f"{question.question_id}.json").read_text(encoding="utf-8")
    )
    protocol_deviations = [
        event for event in iter_events(measurement_dir) if event["event_type"] == "protocol_deviation"
    ]

    assert report["status"] == "red"
    assert len(snapshot["orderings"]) == 5
    assert all(len(ordering["ordering"]) == 5 for ordering in snapshot["orderings"])
    assert protocol_deviations
    assert protocol_deviations[0]["payload"]["original_paragraph_count"] == question.paragraph_count
    assert protocol_deviations[0]["payload"]["cohort_paragraph_count"] == 5


def test_phase1_cohort_runner_supports_configurable_calibration_per_hop_count(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")

    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_plan.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["calibration"] = {"per_hop_count": 1}
    payload["question_paragraph_limit"] = 5
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    assert first_report["status"] == "awaiting_annotation"
    assert first_report["summary"]["measurement_status"] == "pilot_only"
    complete_annotation_labels(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    calibration_manifest = json.loads(calibration_manifest_path.read_text(encoding="utf-8"))

    assert report["status"] == "green"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert report["summary"]["calibration_per_hop_count"] == 1
    assert report["summary"]["model_roles"]["small"]["planned"] == 3
    assert report["summary"]["model_roles"]["small"]["completed"] == 3
    assert report["summary"]["model_roles"]["frontier"]["planned"] == 3
    assert report["summary"]["model_roles"]["frontier"]["completed"] == 3
    assert report["summary"]["question_counts"]["small"]["remaining"] == 0
    assert report["summary"]["question_counts"]["frontier"]["remaining"] == 0
    assert calibration_manifest["per_hop_counts"] == {"2hop": 1, "3hop": 1, "4hop": 1}
    assert len(calibration_manifest["selected_questions"]) == 3
    assert {entry["hop_depth"] for entry in calibration_manifest["selected_questions"]} == {
        "2hop",
        "3hop",
        "4hop",
    }


def test_phase1_cohort_runner_does_not_skip_when_preexisting_orderings_match_only_by_id(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = bundle.sample[0]

    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort_plan.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions=[question.question_id],
        frontier_questions=[],
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["question_paragraph_limit"] = 5
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    full_orderings = build_orderings(
        question.question_id,
        [paragraph.paragraph_id for paragraph in question.paragraphs],
        k_lcb=5,
        canonical_ordering_id="canonical_v1",
        seed=20260418,
    )
    shared = {
        "run_id": "preexisting-run",
        "question_id": question.question_id,
        "hop_depth": question.hop_depth,
        "provider": "dashscope",
        "backend_id": "mock_forced_decode",
        "model_id": "qwen3-14b",
        "model_role": "small",
        "manifest_hash": bundle.manifest_hash,
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "request_fingerprint": "fp-full",
        "response_status": "mock",
        "notes": "fixture",
        "payload": {},
    }
    append_event(
        measurement_dir,
        {
            "event_type": "baseline_scored",
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.5,
            **shared,
        },
    )
    for ordering in full_orderings:
        append_event(
            measurement_dir,
            {
                "event_type": "full_scored",
                "ordering_id": ordering.ordering_id,
                "ordering": list(ordering.paragraph_ids),
                "paragraph_id": None,
                "full_logp": -1.2,
                "loo_logp": None,
                "delta_loo": None,
                "baseline_logp": -2.5,
                **shared,
            },
        )
        for paragraph_id in ordering.paragraph_ids:
            append_event(
                measurement_dir,
                {
                    "event_type": "loo_scored",
                    "ordering_id": ordering.ordering_id,
                    "ordering": list(ordering.paragraph_ids),
                    "paragraph_id": paragraph_id,
                    "full_logp": -1.2,
                    "loo_logp": -1.4,
                    "delta_loo": 0.2,
                    "baseline_logp": -2.5,
                    **shared,
                },
            )
            append_event(
                measurement_dir,
                {
                    "event_type": "ordering_scored",
                    "ordering_id": ordering.ordering_id,
                    "ordering": list(ordering.paragraph_ids),
                    "paragraph_id": paragraph_id,
                    "full_logp": -1.2,
                    "loo_logp": -1.4,
                    "delta_loo": 0.2,
                    "baseline_logp": -2.5,
                    **shared,
                },
            )

    before_baselines = [
        event
        for event in iter_events(measurement_dir)
        if event["event_type"] == "baseline_scored" and event.get("model_role") == "small"
    ]

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    after_baselines = [
        event
        for event in iter_events(measurement_dir)
        if event["event_type"] == "baseline_scored" and event.get("model_role") == "small"
    ]
    snapshot = json.loads(
        (measurement_dir / "questions" / "small" / f"{question.question_id}.json").read_text(encoding="utf-8")
    )

    assert report["status"] == "red"
    assert len(before_baselines) == 1
    assert len(after_baselines) == 2
    assert len(snapshot["orderings"]) == 5
    assert all(len(ordering["ordering"]) == 5 for ordering in snapshot["orderings"])


def test_phase1_cohort_runner_writes_blocked_questions_and_replaces_on_rerun(workspace_tmp_dir, monkeypatch):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "live_calibration_p2" / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "live_calibration_p2_plan.json"
    _write_plan(
        plan_path,
        measurement_dir=measurement_dir,
        export_dir=export_dir,
        checkpoint_dir=checkpoint_dir,
        cache_dir=cache_dir,
        calibration_manifest_path=calibration_manifest_path,
        small_questions="calibration_manifest",
        frontier_questions="calibration_manifest",
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["backend"] = "live"
    payload["question_paragraph_limit"] = 5
    payload["calibration"] = {"per_hop_count": 2}
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    blocked_question_id = "2hop__86458_20273"
    state = {"blocked_once": False}

    class BlockingMockBackend(MockScoringBackend):
        backend_id = "dashscope_openai_chat"
        provider_name = "dashscope"

        def score_answer(self, question_text, answer_text, ordered_paragraphs):
            if (
                not state["blocked_once"]
                and "founder of the Presbyterian Church" in question_text
            ):
                state["blocked_once"] = True
                raise RuntimeError(
                    'DashScope request failed with HTTP 400: {"error":{"code":"data_inspection_failed"}}'
                )
            return super().score_answer(question_text, answer_text, ordered_paragraphs)

    def _fake_build_backend(context, backend_name, model_role):
        if backend_name != "live":
            raise AssertionError("blocked rerun test expects live backend flow")
        return BlockingMockBackend(model_id=context.models[model_role].model)

    monkeypatch.setattr(phase1_run_module, "_build_backend", _fake_build_backend)

    first_report = run_phase1_cohort(
        backend_name="live",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    blocked_questions_path = calibration_manifest_path.parent / "blocked_questions.json"
    blocked_payload = json.loads(blocked_questions_path.read_text(encoding="utf-8"))
    protocol_deviations = [
        event
        for event in iter_events(measurement_dir)
        if event["event_type"] == "protocol_deviation"
        and event.get("payload", {}).get("error_code") == "data_inspection_failed"
    ]

    assert first_report["status"] == "blocked_replan_required"
    assert first_report["blocked_question_id"] == blocked_question_id
    assert blocked_questions_path.exists()
    assert blocked_payload["blocked_question_ids"] == [blocked_question_id]
    assert protocol_deviations

    second_report = run_phase1_cohort(
        backend_name="live",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    assert second_report["status"] == "awaiting_annotation"
    assert second_report["summary"]["measurement_status"] == "pilot_only"
    complete_annotation_labels(second_report["annotation_manifest_path"])

    third_report = run_phase1_cohort(
        backend_name="live",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    calibration_manifest = json.loads(calibration_manifest_path.read_text(encoding="utf-8"))
    selected_2hop = [
        entry["question_id"]
        for entry in calibration_manifest["selected_questions"]
        if entry["hop_depth"] == "2hop"
    ]

    assert third_report["status"] == "green"
    assert third_report["summary"]["pipeline_status"] == "pipeline_validated"
    assert third_report["summary"]["measurement_status"] == "pilot_only"
    assert third_report["summary"]["model_roles"]["small"]["planned"] == 6
    assert third_report["summary"]["model_roles"]["small"]["completed"] == 6
    assert third_report["summary"]["model_roles"]["frontier"]["planned"] == 6
    assert third_report["summary"]["model_roles"]["frontier"]["completed"] == 6
    assert blocked_question_id not in selected_2hop
    assert selected_2hop == ["2hop__132929_684936", "2hop__32254_84601"]


def test_resolve_question_ids_excludes_blocked_questions_from_all_selection():
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    blocked_question_id = bundle.sample[0].question_id

    resolved_question_ids = phase1_run_module._resolve_question_ids(
        "all",
        [],
        bundle,
        exclude_question_ids=(blocked_question_id,),
    )

    assert blocked_question_id not in resolved_question_ids
    assert len(resolved_question_ids) == len(bundle.sample) - 1
