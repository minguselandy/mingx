from phase0.measurement_store import (
    append_event,
    iter_events,
    materialize_question_snapshot,
    rebuild_run_progress,
    snapshot_path_for,
)


def test_measurement_store_appends_events_in_order(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"
    base_event = {
        "run_id": "run-smoke",
        "question_id": "2hop__256778_131879",
        "hop_depth": "2hop",
        "model_id": "claude-haiku-4-5-20251001",
        "ordering_id": None,
        "ordering": None,
        "paragraph_id": None,
        "full_logp": None,
        "loo_logp": None,
        "delta_loo": None,
        "baseline_logp": -2.5,
        "manifest_hash": "manifest-sha",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "notes": "fixture",
    }

    append_event(store_dir, {"event_type": "run_started", **base_event})
    append_event(store_dir, {"event_type": "baseline_scored", **base_event})

    events = list(iter_events(store_dir))

    assert [event["event_type"] for event in events] == ["run_started", "baseline_scored"]
    assert events[0]["event_id"] != events[1]["event_id"]


def test_materialize_question_snapshot_matches_phase1_b5_shape(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"
    shared = {
        "run_id": "run-smoke",
        "question_id": "2hop__256778_131879",
        "hop_depth": "2hop",
        "model_id": "claude-haiku-4-5-20251001",
        "manifest_hash": "manifest-sha",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "notes": "fixture",
    }

    append_event(
        store_dir,
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
    append_event(
        store_dir,
        {
            "event_type": "ordering_scored",
            "ordering_id": "canonical",
            "ordering": [0, 1, 2],
            "paragraph_id": 0,
            "full_logp": -1.2,
            "loo_logp": -1.6,
            "delta_loo": 0.4,
            "baseline_logp": -2.5,
            **shared,
        },
    )
    append_event(
        store_dir,
        {
            "event_type": "ordering_scored",
            "ordering_id": "canonical",
            "ordering": [0, 1, 2],
            "paragraph_id": 1,
            "full_logp": -1.2,
            "loo_logp": -1.3,
            "delta_loo": 0.1,
            "baseline_logp": -2.5,
            **shared,
        },
    )

    snapshot = materialize_question_snapshot(store_dir, "2hop__256778_131879")

    assert snapshot["question_id"] == "2hop__256778_131879"
    assert snapshot["hop_depth"] == "2hop"
    assert snapshot["V_model"] == "claude-haiku-4-5-20251001"
    assert snapshot["baseline_logp"] == -2.5
    assert snapshot["orderings"] == [
        {
            "ordering_id": "canonical",
            "ordering": [0, 1, 2],
            "paragraphs": [
                {"paragraph_id": 0, "full_logp": -1.2, "loo_logp": -1.6, "delta_loo": 0.4},
                {"paragraph_id": 1, "full_logp": -1.2, "loo_logp": -1.3, "delta_loo": 0.1},
            ],
        }
    ]
    assert snapshot["delta_loo_LCB"] == [
        {"paragraph_id": 0, "delta_loo": 0.4},
        {"paragraph_id": 1, "delta_loo": 0.1},
    ]


def test_rebuild_run_progress_uses_event_log_as_source_of_truth(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"
    shared = {
        "run_id": "run-smoke",
        "question_id": "2hop__256778_131879",
        "hop_depth": "2hop",
        "provider": "dashscope",
        "backend_id": "mock",
        "model_id": "qwen3-14b",
        "manifest_hash": "manifest-sha",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "request_fingerprint": "fingerprint",
        "response_status": "mock",
        "notes": "fixture",
        "payload": {},
    }

    append_event(
        store_dir,
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
    append_event(
        store_dir,
        {
            "event_type": "full_scored",
            "ordering_id": "canonical_v1",
            "ordering": [0, 1, 2],
            "paragraph_id": None,
            "full_logp": -1.2,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.5,
            **shared,
        },
    )
    append_event(
        store_dir,
        {
            "event_type": "loo_scored",
            "ordering_id": "canonical_v1",
            "ordering": [0, 1, 2],
            "paragraph_id": 0,
            "full_logp": -1.2,
            "loo_logp": -1.6,
            "delta_loo": 0.4,
            "baseline_logp": -2.5,
            **shared,
        },
    )

    progress = rebuild_run_progress(store_dir, run_id="run-smoke")

    assert progress["source_of_truth"] == "event_log"
    assert progress["baseline_scored_questions"] == ["2hop__256778_131879"]
    assert progress["full_scored_units"] == [("2hop__256778_131879", "canonical_v1")]
    assert progress["loo_scored_units"] == [("2hop__256778_131879", "canonical_v1", 0)]


def test_materialize_question_snapshot_isolated_by_model_role(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"
    shared = {
        "run_id": "run-smoke",
        "question_id": "2hop__256778_131879",
        "hop_depth": "2hop",
        "manifest_hash": "manifest-sha",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "notes": "fixture",
    }

    append_event(
        store_dir,
        {
            "event_type": "baseline_scored",
            "model_id": "qwen3-14b",
            "model_role": "small",
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
    append_event(
        store_dir,
        {
            "event_type": "ordering_scored",
            "model_id": "qwen3-14b",
            "model_role": "small",
            "ordering_id": "canonical_v1",
            "ordering": [0, 1],
            "paragraph_id": 0,
            "full_logp": -1.2,
            "loo_logp": -1.6,
            "delta_loo": 0.4,
            "baseline_logp": -2.5,
            **shared,
        },
    )
    append_event(
        store_dir,
        {
            "event_type": "baseline_scored",
            "model_id": "qwen3-32b",
            "model_role": "frontier",
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -3.5,
            **shared,
        },
    )
    append_event(
        store_dir,
        {
            "event_type": "ordering_scored",
            "model_id": "qwen3-32b",
            "model_role": "frontier",
            "ordering_id": "canonical_v1",
            "ordering": [0, 1],
            "paragraph_id": 0,
            "full_logp": -2.2,
            "loo_logp": -2.9,
            "delta_loo": 0.7,
            "baseline_logp": -3.5,
            **shared,
        },
    )

    small_snapshot = materialize_question_snapshot(store_dir, "2hop__256778_131879", model_role="small")
    frontier_snapshot = materialize_question_snapshot(
        store_dir,
        "2hop__256778_131879",
        model_role="frontier",
    )

    assert small_snapshot["model_role"] == "small"
    assert frontier_snapshot["model_role"] == "frontier"
    assert small_snapshot["baseline_logp"] == -2.5
    assert frontier_snapshot["baseline_logp"] == -3.5
    assert snapshot_path_for(store_dir, "2hop__256778_131879", "small").exists()
    assert snapshot_path_for(store_dir, "2hop__256778_131879", "frontier").exists()
