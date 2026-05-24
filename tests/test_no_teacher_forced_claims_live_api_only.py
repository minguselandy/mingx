from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LIVE_API_BOUNDARY_DOCS = (
    ROOT / "docs" / "api" / "live-api-capability-contract.md",
    ROOT / "docs" / "paper" / "live-api-experiment-boundaries.md",
    ROOT / "docs" / "roadmaps" / "live-api-only-development-plan.md",
    ROOT / "docs" / "paper" / "v12-live-api-operational-paper-claim-table.md",
    ROOT / "docs" / "paper" / "v12-evidence-ledger.md",
)

DENIAL_MARKERS = (
    "blocked",
    "candidate",
    "cannot",
    "denied",
    "denies",
    "diagnostic",
    "does not",
    "fail-closed",
    "failed",
    "failed_closed",
    "false",
    "locked",
    "must not",
    "no ",
    "not ",
    "only",
    "operational",
    "remain false",
    "rejected",
    "stop",
    "unavailable",
    "without",
    "| false |",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _windows(text: str, pattern: str, *, radius: int = 420) -> list[str]:
    lower = text.lower()
    return [
        lower[max(0, match.start() - radius) : match.end() + radius]
        for match in re.finditer(pattern, lower, flags=re.IGNORECASE)
    ]


def test_live_api_docs_reject_teacher_forced_and_bridge_claims() -> None:
    failures: list[str] = []
    patterns = {
        "teacher-forced nll support": r"teacher-forced nll support",
        "fixed-target continuation scoring": r"fixed-target continuation scoring",
        "metric bridge support": r"metric bridge support",
        "measurement validation": r"measurement validation",
        "human/external gold": r"human/external gold",
        "calibrated_proxy_supported": r"calibrated_proxy_supported",
        "vinfo_proxy_supported": r"vinfo_proxy_supported",
        "selector superiority": r"selector superiority",
        "route 5 unlock": r"route 5 unlock",
        "route 8 unlock": r"route 8 unlock",
    }

    for path in LIVE_API_BOUNDARY_DOCS:
        text = _read(path)
        for label, pattern in patterns.items():
            for window in _windows(text, pattern):
                if not any(marker in window for marker in DENIAL_MARKERS):
                    failures.append(f"{path.relative_to(ROOT)}::{label}")

    assert not failures, sorted(set(failures))


def test_live_api_docs_do_not_describe_generated_logprobs_as_fixed_target_scores() -> None:
    text = "\n".join(_read(path) for path in LIVE_API_BOUNDARY_DOCS).lower()

    unsafe_phrases = (
        "generated-token chat logprobs are teacher-forced nll",
        "generated output-token logprobs are teacher-forced nll",
        "chat logprobs are fixed-target continuation scoring",
        "generated-token chat logprobs provide fixed-target continuation scoring",
        "generated-token chat logprobs provide metric bridge support",
        "constrained label generation is metric bridge support",
        "model-adjudicated silver labels are human/external gold",
        "operational replay is global selector superiority",
        "epf-final validates the paper: true",
    )
    for phrase in unsafe_phrases:
        assert phrase not in text


def test_live_api_docs_make_backend_limitation_explicit() -> None:
    text = "\n".join(_read(path) for path in LIVE_API_BOUNDARY_DOCS).lower()

    assert "generated output-token logprobs are answer-side confidence diagnostics only" in text
    assert "not fixed-target teacher-forced nll" in text
    assert "not fixed-target continuation scoring" in text
    assert "route 5 locked: true" in text
    assert "route 8 locked: true" in text
