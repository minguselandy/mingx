from __future__ import annotations

from cps.analysis.contamination_audit import build_contamination_report
from cps.experiments.workbench.dynamic_holdout import build_dynamic_holdout_readiness


def test_contamination_and_holdout_layer_reports_candidate_readiness_without_unlock() -> None:
    report = build_contamination_report(
        datasets=[
            {"dataset": "HotpotQA", "source_kind": "public_benchmark", "split": "dev_distractor"},
            {"dataset": "ProjectNativeRealisticTasks", "source_kind": "fixture", "split": "fixture_v12"},
        ]
    )
    holdout = build_dynamic_holdout_readiness(report)

    assert report["raw_dataset_mirrors_created"] is False
    assert report["claim_upgrade_allowed"] is False
    assert holdout["route5_unlocked"] is False
    assert holdout["route8_unlocked"] is False
