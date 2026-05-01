import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cps.data.manifest import ManifestParagraph, ManifestQuestion
from cps.runtime.cohort import run_phase1_cohort
from cps.runtime.projection_export import (
    PROJECTION_EVENT_SEQUENCE,
    build_projection_run_id,
    emit_projection_artifact_events,
)
from cps.schema import ProjectionBundleV1
from cps.store.measurement import iter_events
from cps.store.progress import MeasurementUnitSpec


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


def _write_cohort_plan(path: Path, *, workspace_tmp_dir: Path) -> None:
    payload = {
        "experiment_id": "musique_gate1_phase1_v1",
        "protocol_version": "phase1.v1",
        "phase1_config_path": "./phase1.yaml",
        "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
        "hash_path": "./artifacts/phase0/content_hashes.json",
        "calibration_manifest_path": str((workspace_tmp_dir / "calibration_manifest.json").as_posix()),
        "backend": "mock",
        "scoring": {
            "k_lcb": 5,
            "lcb_quantile": 0.1,
        },
        "calibration": {"per_hop_count": 1},
        "question_paragraph_limit": 5,
        "small_full_n": {"questions": "calibration_manifest"},
        "frontier_calibration": {"questions": "calibration_manifest"},
        "storage": {
            "measurement_dir": str((workspace_tmp_dir / "measurements").as_posix()),
            "export_dir": str((workspace_tmp_dir / "exports").as_posix()),
            "checkpoint_dir": str((workspace_tmp_dir / "checkpoints").as_posix()),
            "cache_dir": str((workspace_tmp_dir / "cache").as_posix()),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _context():
    return SimpleNamespace(
        provider=SimpleNamespace(name="dashscope"),
        experiment={
            "id": "musique_gate1_phase1_v1",
            "protocol_version": "phase1.v1",
            "seed": 20260418,
        },
        scoring=SimpleNamespace(
            utility_metric="log_loss",
            canonical_ordering_id="canonical_v1",
        ),
    )


def _backend():
    return SimpleNamespace(
        backend_id="mock_forced_decode",
        model_id="qwen3.6-flash",
        provider_name="dashscope",
    )


def _question():
    return ManifestQuestion(
        question_id="question-1",
        hop_depth="2hop",
        hop_subcategory="bridge",
        question_text="Who wrote the fixture?",
        answer_text="A",
        answer_aliases=("A",),
        answerable=True,
        paragraph_count=2,
        paragraphs=(
            ManifestParagraph(
                paragraph_id=1,
                title="First",
                text="Alpha context paragraph.",
                is_supporting=True,
            ),
            ManifestParagraph(
                paragraph_id=2,
                title="Second",
                text="Beta context paragraph.",
                is_supporting=False,
            ),
        ),
    )


def _spec():
    return MeasurementUnitSpec(
        question_id="question-1",
        hop_depth="2hop",
        model_role="small",
        provider="dashscope",
        backend_id="mock_forced_decode",
        model_id="qwen3.6-flash",
        manifest_hash="manifest-hash",
        ordering_ids=("canonical_v1",),
        paragraph_ids=(1, 2),
        ordering_items=(("canonical_v1", (1, 2)),),
    )


def _snapshot():
    return {
        "question_id": "question-1",
        "hop_depth": "2hop",
        "baseline_logp": -1.0,
        "delta_loo_LCB": [
            {"paragraph_id": 1, "delta_loo": 0.2},
            {"paragraph_id": 2, "delta_loo": 0.1},
        ],
    }


def _projection_run_id():
    return build_projection_run_id(
        experiment_id="musique_gate1_phase1_v1",
        protocol_version="phase1.v1",
        manifest_hash="manifest-hash",
        backend_name="mock",
        scope_mode="pilot_reduced_scope",
        seed=20260418,
        small_question_ids=["question-1"],
        frontier_question_ids=[],
        k_lcb=5,
    )


def _emit_once(store_dir: Path, *, projection_run_id: str | None = None):
    return emit_projection_artifact_events(
        store_dir=store_dir,
        context=_context(),
        backend=_backend(),
        model_role="small",
        spec=_spec(),
        question=_question(),
        snapshot=_snapshot(),
        manifest_hash="manifest-hash",
        cohort_run_id="cohort-run-volatile",
        projection_run_id=projection_run_id if projection_run_id is not None else _projection_run_id(),
        scope_mode="pilot_reduced_scope",
        k_lcb=5,
        source_mode="mock",
    )


def _projection_events(store_dir: Path) -> list[dict]:
    return [
        event
        for event in iter_events(store_dir)
        if event["event_type"] in PROJECTION_EVENT_SEQUENCE
    ]


def test_helper_emits_required_projection_events_in_order(workspace_tmp_dir):
    _emit_once(workspace_tmp_dir / "measurements")

    events = _projection_events(workspace_tmp_dir / "measurements")

    assert [event["event_type"] for event in events] == list(PROJECTION_EVENT_SEQUENCE)
    for event in events:
        payload = event["payload"]
        assert payload["run_id"] == _projection_run_id()
        assert payload["dispatch_id"] == "question-1:small"
        assert payload["agent_id"] == "small"
        assert payload["round_id"] == "canonical_v1:k_lcb_5"


def test_missing_identity_is_rejected_before_projection_events_are_appended(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"

    with pytest.raises(ValueError, match="run_id is required"):
        _emit_once(store_dir, projection_run_id="")

    assert _projection_events(store_dir) == []


def test_projection_bundle_event_has_reconstructable_canonical_hash(workspace_tmp_dir):
    bundle, canonical_hash = _emit_once(workspace_tmp_dir / "measurements")

    bundle_events = [
        event
        for event in _projection_events(workspace_tmp_dir / "measurements")
        if event["event_type"] == "projection_bundle_materialized"
    ]
    payload = bundle_events[0]["payload"]
    reconstructed = ProjectionBundleV1.from_dict(payload)

    assert payload["canonical_hash"] == canonical_hash == bundle.canonical_hash()
    assert reconstructed.canonical_hash() == canonical_hash
    assert reconstructed.metric_bridge_witness["diagnostic_claim_level"] == "operational_utility_only"


def test_projection_event_payloads_are_deterministic_across_repeated_offline_runs(workspace_tmp_dir):
    first_store = workspace_tmp_dir / "first"
    second_store = workspace_tmp_dir / "second"

    _emit_once(first_store)
    _emit_once(second_store)

    first_payloads = [(event["event_type"], event["payload"]) for event in _projection_events(first_store)]
    second_payloads = [(event["event_type"], event["payload"]) for event in _projection_events(second_store)]

    assert first_payloads == second_payloads


def test_mock_cohort_emits_projection_bundle_per_completed_dispatch(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    plan_path = workspace_tmp_dir / "cohort.json"
    _write_env(env_path)
    _write_cohort_plan(plan_path, workspace_tmp_dir=workspace_tmp_dir)

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    events = list(iter_events(workspace_tmp_dir / "measurements"))
    projection_events = [event for event in events if event["event_type"] in PROJECTION_EVENT_SEQUENCE]
    bundle_events = [
        event for event in projection_events if event["event_type"] == "projection_bundle_materialized"
    ]
    completed = sum(role["completed"] for role in report["summary"]["model_roles"].values())

    assert report["status"] == "awaiting_annotation"
    assert Path(report["run_summary_path"]).exists()
    assert report["summary"]["source_of_truth"] == "event_log"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert report["summary"]["annotation_mode"] == "awaiting_labels"
    assert report["summary"]["bridge_status"] == "computed"
    assert completed == 6
    assert len(bundle_events) == completed
    assert len(projection_events) == completed * len(PROJECTION_EVENT_SEQUENCE)
    assert all(event["backend_id"] == "mock_forced_decode" for event in projection_events)
    assert all(
        event["payload"].get("metric_bridge_witness", {}).get("diagnostic_claim_level")
        != "measurement_validated"
        for event in bundle_events
    )
    assert "reference/" not in json.dumps(
        [event["payload"] for event in projection_events],
        ensure_ascii=False,
        sort_keys=True,
    )
