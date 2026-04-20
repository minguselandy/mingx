from __future__ import annotations

from cps.analysis.reliability import compute_reliability_summary


def test_compute_reliability_summary_reports_kappa_ci_and_tier():
    rows = [
        {
            "annotation_item_id": f"item-{index}",
            "question_id": f"q-{index // 2}",
            "hop_depth": hop_depth,
            "source": "flagged",
            "automated_label": label,
            "primary_a_label": label,
            "primary_b_label": label,
            "expert_label": label,
        }
        for index, (hop_depth, label) in enumerate(
            [
                ("2hop", "HIGH"),
                ("2hop", "LOW"),
                ("3hop", "BUFFER"),
                ("3hop", "HIGH"),
                ("4hop", "LOW"),
                ("4hop", "BUFFER"),
            ]
        )
    ]

    summary = compute_reliability_summary(
        annotation_rows=rows,
        annotation_mode="synthetic_passthrough",
        seed=20260418,
        bootstrap_resamples=40,
        threshold=0.7,
    )

    assert summary["status"] == "computed"
    assert summary["annotation_mode"] == "synthetic_passthrough"
    assert summary["scientific_consumption_allowed"] is False
    assert summary["threshold"]["value"] == 0.7
    assert summary["threshold"]["source_document"] == "execution-readiness-checklist.md"
    assert summary["pooled"]["kappa_primary"]["point_estimate"] == 1.0
    assert summary["pooled"]["kappa_automated_expert"]["point_estimate"] == 1.0
    assert summary["per_hop"]["2hop"]["kappa_primary"]["point_estimate"] == 1.0
    assert summary["tier_classification"]["tier"] == "tier1_unconditional_pass"
