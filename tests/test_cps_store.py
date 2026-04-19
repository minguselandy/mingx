from cps.store.measurement import append_event, iter_events, materialize_question_snapshot


def test_cps_measurement_store_appends_and_materializes(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "measurements"
    shared = {
        "run_id": "cps-store-test",
        "question_id": "q1",
        "hop_depth": "2hop",
        "provider": "dashscope",
        "backend_id": "mock_forced_decode",
        "model_id": "qwen3-14b",
        "model_role": "small",
        "manifest_hash": "manifest-hash",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "request_fingerprint": "fp",
        "response_status": "mock",
        "notes": "fixture",
        "payload": {},
    }
    ordering = [0, 1]

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
            "baseline_logp": -2.0,
            **shared,
        },
    )
    append_event(
        store_dir,
        {
            "event_type": "full_scored",
            "ordering_id": "canonical_v1",
            "ordering": ordering,
            "paragraph_id": None,
            "full_logp": -1.2,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.0,
            **shared,
        },
    )
    for paragraph_id, loo_logp, delta_loo in ((0, -1.4, 0.2), (1, -1.5, 0.3)):
        append_event(
            store_dir,
            {
                "event_type": "loo_scored",
                "ordering_id": "canonical_v1",
                "ordering": ordering,
                "paragraph_id": paragraph_id,
                "full_logp": -1.2,
                "loo_logp": loo_logp,
                "delta_loo": delta_loo,
                "baseline_logp": -2.0,
                **shared,
            },
        )
        append_event(
            store_dir,
            {
                "event_type": "ordering_scored",
                "ordering_id": "canonical_v1",
                "ordering": ordering,
                "paragraph_id": paragraph_id,
                "full_logp": -1.2,
                "loo_logp": loo_logp,
                "delta_loo": delta_loo,
                "baseline_logp": -2.0,
                **shared,
            },
        )

    snapshot = materialize_question_snapshot(store_dir, "q1", model_role="small", lcb_quantile=0.1)
    events = list(iter_events(store_dir))

    assert snapshot["question_id"] == "q1"
    assert snapshot["model_role"] == "small"
    assert len(snapshot["delta_loo_LCB"]) == 2
    assert events[-1]["event_type"] == "question_materialized"
