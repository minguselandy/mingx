from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OPERATIONAL_EVALUATION_DOC = ROOT / "docs" / "paper" / "live-api-operational-evaluation-section.md"
REVIEWER_DEFENSE_DOC = ROOT / "docs" / "paper" / "reviewer-defense-live-api-only.md"
RELATED_WORK_DOC = ROOT / "docs" / "paper" / "related-work-live-api-operational-audit.md"
CHECKLIST_DOC = ROOT / "docs" / "paper" / "v12-manuscript-integration-checklist.md"

PAPER_LAPI_DOCS = (
    OPERATIONAL_EVALUATION_DOC,
    REVIEWER_DEFENSE_DOC,
    RELATED_WORK_DOC,
    CHECKLIST_DOC,
)

DENIAL_MARKERS = (
    "blocked",
    "candidate",
    "cannot",
    "denied",
    "diagnostic",
    "do not",
    "does not",
    "false",
    "keep ",
    "locked",
    "must not",
    "no ",
    "not ",
    "only",
    "operational",
    "unsupported",
    "without",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _combined_text() -> str:
    return "\n".join(_read(path) for path in PAPER_LAPI_DOCS).lower()


def _windows(text: str, pattern: str, *, radius: int = 420) -> list[str]:
    lower = text.lower()
    return [
        lower[max(0, match.start() - radius) : match.end() + radius]
        for match in re.finditer(pattern, lower, flags=re.IGNORECASE)
    ]


def test_lapi8_paper_docs_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in PAPER_LAPI_DOCS if not path.exists()]
    assert not missing


def test_operational_evaluation_section_uses_required_stance() -> None:
    text = _read(OPERATIONAL_EVALUATION_DOC).lower()
    first_heading = text.splitlines()[0]

    assert first_heading == "# operational evaluation and weak-evidence diagnostics"
    assert "validation" not in first_heading
    for required in (
        "live-api-only",
        "audit-first",
        "claim-gated",
        "formal v-information anchor only",
        "current experiments do not estimate a fixed-target bridge",
        "hard replay evidence is separated from weak model-adjudicated evidence",
        "operational diagnostics or candidate evidence only",
        "teacher-forced nll support: false",
        "fixed-target continuation scoring support: false",
        "route 5 locked: true",
        "route 8 locked: true",
    ):
        assert required in text


def test_reviewer_defense_answers_required_questions_without_upgrading_claims() -> None:
    text = _read(REVIEWER_DEFENSE_DOC).lower()

    for question in (
        "why no teacher-forced nll?",
        "why mention v-information?",
        "what is the contribution without a bridge?",
        "why use llm judges?",
        "why not claim superior router/selector?",
    ):
        assert question in text

    assert "generated-token chat logprobs are answer-side confidence diagnostics only" in text
    assert "the formal v-information objective is the anchor, not a current deployed measurement claim" in text
    assert "llm judges are weak-source candidate diagnostics" in text
    assert "no superior router or selector claim is made" in text


def test_related_work_frames_live_api_package_as_audit_protocol_not_validation() -> None:
    text = _read(RELATED_WORK_DOC).lower()

    for required in (
        "audit-first operational evaluation",
        "structured extraction and faithfulness",
        "llm judges and weak supervision",
        "live-api operational audit",
        "not measurement validation",
        "not metric bridge support",
        "not selector superiority",
    ):
        assert required in text


def test_checklist_tracks_lapi8_docs_and_completed_lapi_package() -> None:
    text = _read(CHECKLIST_DOC).lower()

    for required in (
        "live-api-operational-evaluation-section.md",
        "reviewer-defense-live-api-only.md",
        "related-work-live-api-operational-audit.md",
        "lapi-1",
        "lapi-2",
        "lapi-3",
        "lapi-4",
        "lapi-5",
        "lapi-6",
        "lapi-7",
        "operational evaluation and weak-evidence diagnostics",
    ):
        assert required in text


def test_paper_live_api_language_keeps_forbidden_claims_qualified() -> None:
    failures: list[str] = []
    patterns = {
        "measurement validation": r"measurement validation",
        "metric bridge support": r"metric bridge support",
        "calibrated proxy support": r"calibrated proxy support|calibrated_proxy_supported",
        "v-information proxy support": r"v-information proxy support|vinfo_proxy_supported",
        "paper evidence": r"paper evidence",
        "selector superiority": r"selector superiority|superior router|superior selector",
        "teacher-forced nll": r"teacher-forced nll",
        "fixed-target continuation scoring": r"fixed-target continuation scoring",
        "route 5 unlock": r"route 5 unlock",
        "route 8 unlock": r"route 8 unlock",
    }

    for path in PAPER_LAPI_DOCS:
        text = _read(path)
        for label, pattern in patterns.items():
            for window in _windows(text, pattern):
                if not any(marker in window for marker in DENIAL_MARKERS):
                    failures.append(f"{path.relative_to(ROOT)}::{label}")

    assert not failures, sorted(set(failures))


def test_paper_live_api_docs_do_not_activate_unsafe_phrases() -> None:
    text = _combined_text()

    unsafe_phrases = (
        "live-api results validate",
        "live-api outputs validate",
        "epf-final validates the paper: true",
        "generated-token chat logprobs are teacher-forced nll",
        "chat logprobs are fixed-target continuation scoring",
        "fixed-target bridge is estimated",
        "metric bridge support is established",
        "v-information proxy support is established",
        "selector superiority is established",
        "route 5 unlocked",
        "route 8 unlocked",
    )
    for phrase in unsafe_phrases:
        assert phrase not in text
