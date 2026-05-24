from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTRACT_DOCS = (
    ROOT / "docs" / "api" / "live-api-capability-contract.md",
    ROOT / "docs" / "paper" / "live-api-experiment-boundaries.md",
    ROOT / "docs" / "roadmaps" / "live-api-only-development-plan.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _combined_contract_text() -> str:
    return "\n".join(_read(path) for path in CONTRACT_DOCS).lower()


def test_live_api_contract_documents_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in CONTRACT_DOCS if not path.exists()]
    assert not missing


def test_live_api_contract_records_allowed_and_denied_capabilities() -> None:
    text = _combined_contract_text()

    for allowed in (
        "dashscope-compatible live api",
        "generated output-token logprobs",
        "answer-side confidence diagnostics",
        "constrained label generation",
        "candidate proxy only",
        "model-adjudicated weak labels",
        "candidate operational evidence",
        "replayable artifact evidence",
    ):
        assert allowed in text

    for denied in (
        "local hf",
        "torch",
        "transformers scorer",
        "vllm",
        "prompt_logprobs support",
        "fixed-target teacher-forced nll",
        "fixed-target continuation scoring",
        "metric bridge support",
        "calibrated_proxy_supported",
        "vinfo_proxy_supported",
        "measurement validation",
        "human/external gold validation",
        "paper-grade evidence",
        "selector superiority",
        "route 5 unlock",
        "route 8 unlock",
    ):
        assert denied in text


def test_live_api_contract_preserves_route_locks_and_claim_ceiling() -> None:
    text = _combined_contract_text()

    assert "operational_utility_only/no_claim_upgrade" in text
    assert "route 5 locked: true" in text
    assert "route 8 locked: true" in text
    assert "route 5 unlock: false" in text
    assert "route 8 unlock: false" in text


def test_live_api_contract_does_not_upgrade_epf_final() -> None:
    text = _combined_contract_text()

    assert "epf-final validates the paper: false" in text
    assert "epf-final is candidate operational evidence only" in text
    assert "raw api responses stored: false" in text
    assert "human/external gold labels available: false" in text
