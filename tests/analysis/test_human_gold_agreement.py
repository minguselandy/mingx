from __future__ import annotations

from cps.analysis.human_gold_agreement import build_human_gold_manifest
from cps.analysis.human_gold_agreement import compute_agreement_report


def test_human_gold_agreement_blocks_when_manifest_unavailable() -> None:
    manifest = build_human_gold_manifest([])
    report = compute_agreement_report([], [])

    assert manifest["human_external_gold_available"] is False
    assert report["status"] == "blocked_no_human_external_gold"
    assert report["measurement_validation_allowed"] is False
