#!/usr/bin/env python3
"""Validate Lightweight Agentic Development Framework state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


KNOWN_STATUSES = {
    "READY",
    "IN_PROGRESS",
    "SELF_CHECK",
    "REVIEW",
    "ACCEPTED",
    "NEXT_PHASE",
    "REQUEST_CHANGES",
    "BLOCKED_OPERATOR_REQUIRED",
    "REJECTED",
    "LIVE_API_REQUIRED",
    "HUMAN_REVIEW_REQUIRED",
    "EXTERNAL_SERVICE_REQUIRED",
    "CREDENTIAL_REQUIRED",
    "LICENSE_REVIEW_REQUIRED",
    "SCIENTIFIC_CLAIM_REQUIRED",
    "SECURITY_REVIEW_REQUIRED",
}

STOP_STATUSES = {
    "BLOCKED_OPERATOR_REQUIRED",
    "REJECTED",
    "REQUEST_CHANGES",
    "LIVE_API_REQUIRED",
    "HUMAN_REVIEW_REQUIRED",
    "EXTERNAL_SERVICE_REQUIRED",
    "CREDENTIAL_REQUIRED",
    "LICENSE_REVIEW_REQUIRED",
    "SCIENTIFIC_CLAIM_REQUIRED",
    "SECURITY_REVIEW_REQUIRED",
}

VERDICTS = {
    "ACCEPT",
    "ACCEPT_WITH_NOTES",
    "REQUEST_CHANGES",
    "BLOCKED_OPERATOR_REQUIRED",
    "REJECT",
}

ACCEPTING_VERDICTS = {"ACCEPT", "ACCEPT_WITH_NOTES"}

FRAMEWORK_REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "LICENSE_NOTES.md",
    "docs/overview.md",
    "docs/state-machine.md",
    "docs/review-protocol.md",
    "docs/role-specs.md",
    "docs/safety-policy.md",
    "docs/integration-guide.md",
    "docs/reference-project-analysis.md",
    "docs/reviews/BOOTSTRAP-review.md",
    "prompts/00-bootstrap-framework.md",
    "prompts/01-initialize-project.md",
    "prompts/02-run-current-phase.md",
    "prompts/03-review-current-phase.md",
    "prompts/04-advance-phase.md",
    "templates/AGENTS.template.md",
    "templates/phase-plan.template.md",
    "templates/phase-review.template.md",
    "templates/current_phase.template.json",
    "templates/phase_history.template.jsonl",
    "templates/automation-config.template.json",
    "scripts/framework_guard.py",
    "scripts/init_project_framework.py",
    ".state/codex/current_phase.json",
    ".state/codex/phase_history.jsonl",
]

TARGET_REQUIRED_FILES = [
    "AGENTS.md",
    "docs/reviews/README.md",
    "docs/reviews/templates/phase-review-template.md",
    ".state/codex/current_phase.json",
    ".state/codex/phase_history.jsonl",
]

TARGET_REQUIRED_ALTERNATIVES = [
    (
        "phase plan",
        [
            "docs/phase-plan.md",
            "docs/automation/phase-plan.md",
            "docs/cps-phase-development-plan.md",
        ],
    ),
    (
        "review protocol",
        [
            "docs/review-protocol.md",
            "docs/automation/review-protocol.md",
            "docs/cps-phase-review-protocol.md",
        ],
    ),
    (
        "guard script",
        [
            "scripts/framework_guard.py",
            "scripts/codex_phase_guard.py",
        ],
    ),
]

FRAMEWORK_MARKERS = [
    "prompts",
    "templates",
    "scripts/init_project_framework.py",
    "docs/overview.md",
]

BOOL_FIELDS = ["safe_auto_advance", "blocked", "requires_operator"]
OPTIONAL_BOOL_FIELDS = ["next_phase_safe_auto_advance", "next_phase_requires_operator"]

SAFE_TEXT_VALUES = {"none", "no", "no impact"}
REQUIRED_METADATA_FIELDS = {
    "phase_id",
    "verdict",
    "next_phase_allowed",
    "next_phase_id",
    "license_impact",
    "safety_impact",
    "dependency_changes",
    "live_api_required",
    "external_service_required",
    "credential_required",
    "human_review_required",
    "scientific_claim_required",
    "operator_required",
}

SAFE_TEXT_METADATA_FIELDS = ["license_impact", "safety_impact", "dependency_changes"]
SAFE_FALSE_METADATA_FIELDS = [
    "live_api_required",
    "external_service_required",
    "credential_required",
    "human_review_required",
    "scientific_claim_required",
    "operator_required",
]


def project_root(root_arg: str | None = None) -> Path:
    if root_arg:
        return Path(root_arg).resolve()
    cwd = Path.cwd()
    if (cwd / ".state" / "codex").exists() or (cwd / "AGENTS.md").exists():
        return cwd.resolve()
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def current_phase_path(root: Path) -> Path:
    return root / ".state" / "codex" / "current_phase.json"


def history_path(root: Path) -> Path:
    return root / ".state" / "codex" / "phase_history.jsonl"


def normalize_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def parse_bool_text(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = normalize_scalar(value).lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    return None


def extract_field(text: str, field: str) -> str | None:
    pattern = re.compile(rf"^\s*(?:[-*]\s*)?{re.escape(field)}\s*:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    return normalize_scalar(match.group(1))


def extract_metadata_block(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    start: int | None = None
    fence = ""
    for index, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in {"```yaml", "```yml"}:
            start = index + 1
            fence = line.strip()[:3]
            break
    if start is None:
        return None

    collected: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith(fence):
            return parse_yaml_like(collected)
        collected.append(line)
    return None


def parse_yaml_like(lines: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        normalized_key = key.strip().lower()
        if normalized_key:
            metadata[normalized_key] = normalize_scalar(value)
    return metadata


def is_framework_profile(root: Path) -> bool:
    return all((root / marker).exists() for marker in FRAMEWORK_MARKERS)


def resolve_profile(root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    return "framework" if is_framework_profile(root) else "target"


def cmd_status(root: Path) -> int:
    path = current_phase_path(root)
    if not path.exists():
        print(f"missing current phase: {path}", file=sys.stderr)
        return 2
    try:
        state = load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid current phase: {exc}", file=sys.stderr)
        return 2

    print(f"phase_id: {state.get('phase_id')}")
    print(f"phase_title: {state.get('phase_title')}")
    print(f"status: {state.get('status')}")
    print(f"blocked: {state.get('blocked')}")
    print(f"requires_operator: {state.get('requires_operator')}")
    print(f"safe_auto_advance: {state.get('safe_auto_advance')}")
    print(f"next_phase_id: {state.get('next_phase_id')}")
    return 0


def validate_history(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing required file: {path}"]
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{index}: invalid JSONL: {exc}")
                continue
            if not isinstance(item, dict):
                errors.append(f"{path}:{index}: JSONL entry must be an object")
    return errors


def validate_required_files(root: Path, profile: str) -> list[str]:
    errors: list[str] = []
    required_files = FRAMEWORK_REQUIRED_FILES if profile == "framework" else TARGET_REQUIRED_FILES
    for relative in required_files:
        if not (root / relative).exists():
            errors.append(f"missing required file: {relative}")

    if profile == "target":
        for label, alternatives in TARGET_REQUIRED_ALTERNATIVES:
            if not any((root / relative).exists() for relative in alternatives):
                errors.append(f"missing required {label}: one of {', '.join(alternatives)}")
    return errors


def validate_current_phase(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    phase_file = current_phase_path(root)
    if not phase_file.exists():
        return None, ["missing current phase JSON"]

    try:
        state = load_json(phase_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, [f"invalid current phase JSON: {exc}"]

    status = state.get("status")
    if status not in KNOWN_STATUSES:
        errors.append(f"unknown status: {status!r}")

    for field in BOOL_FIELDS:
        if not isinstance(state.get(field), bool):
            errors.append(f"{field} must be a boolean")

    for field in OPTIONAL_BOOL_FIELDS:
        if field in state and not isinstance(state.get(field), bool):
            errors.append(f"{field} must be a boolean when present")

    last_review = state.get("last_review")
    if last_review:
        review_path = Path(str(last_review))
        if not review_path.is_absolute():
            review_path = root / review_path
        if review_path.exists():
            try:
                review_text = review_path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"last_review could not be read: {exc}")
            else:
                metadata = extract_metadata_block(review_text)
                verdict = metadata.get("verdict") if metadata else extract_field(review_text, "verdict")
                verdict = verdict.upper() if verdict else None
                if verdict not in VERDICTS:
                    errors.append(f"last_review has invalid verdict: {verdict!r}")
    return state, errors


def validate_template_json(root: Path, profile: str) -> list[str]:
    if profile != "framework":
        return []
    errors: list[str] = []
    for relative in [
        "templates/current_phase.template.json",
        "templates/automation-config.template.json",
    ]:
        path = root / relative
        if path.exists():
            try:
                load_json(path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"invalid template JSON {relative}: {exc}")
    return errors


def cmd_validate(root: Path, profile: str) -> int:
    resolved_profile = resolve_profile(root, profile)
    errors: list[str] = []
    errors.extend(validate_required_files(root, resolved_profile))
    _, phase_errors = validate_current_phase(root)
    errors.extend(phase_errors)
    errors.extend(validate_history(history_path(root)))
    errors.extend(validate_template_json(root, resolved_profile))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"validation passed (profile: {resolved_profile})")
    return 0


def metadata_error(message: str) -> int:
    print(f"cannot advance: {message}")
    return 1


def validate_advance_metadata(metadata: dict[str, str]) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    missing = sorted(REQUIRED_METADATA_FIELDS.difference(metadata))
    if missing:
        errors.append(f"metadata missing required fields: {', '.join(missing)}")

    verdict = metadata.get("verdict")
    normalized_verdict = verdict.upper() if verdict else None
    if normalized_verdict not in VERDICTS:
        errors.append(f"metadata verdict is invalid: {verdict!r}")
    elif normalized_verdict not in ACCEPTING_VERDICTS:
        errors.append(f"review verdict is {normalized_verdict}")

    if parse_bool_text(metadata.get("next_phase_allowed")) is not True:
        errors.append("next_phase_allowed must be true")

    for field in SAFE_TEXT_METADATA_FIELDS:
        value = metadata.get(field)
        if value is None or normalize_scalar(value).lower() not in SAFE_TEXT_VALUES:
            errors.append(f"{field} must be one of: {', '.join(sorted(SAFE_TEXT_VALUES))}")

    for field in SAFE_FALSE_METADATA_FIELDS:
        if parse_bool_text(metadata.get(field)) is not False:
            errors.append(f"{field} must be false")

    for value in metadata.values():
        if normalize_scalar(value).upper() in STOP_STATUSES:
            errors.append(f"metadata indicates stop status: {value}")

    return normalized_verdict, errors


def validate_advance_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    status = state.get("status")
    if status not in KNOWN_STATUSES:
        errors.append(f"unknown current phase status: {status!r}")
    elif status in STOP_STATUSES:
        errors.append(f"current phase status cannot advance: {status}")

    if state.get("blocked") is not False:
        errors.append("current phase blocked must be false")

    if state.get("requires_operator") is not False:
        errors.append("current phase requires_operator must be false")

    if state.get("safe_auto_advance") is not True:
        errors.append("current phase safe_auto_advance must be true")

    if "next_phase_safe_auto_advance" in state and state.get("next_phase_safe_auto_advance") is not True:
        errors.append("next_phase_safe_auto_advance must be true when present")

    if "next_phase_requires_operator" in state and state.get("next_phase_requires_operator") is not False:
        errors.append("next_phase_requires_operator must be false when present")

    return errors


def cmd_can_advance(root: Path, review_path: Path) -> int:
    if not review_path.is_absolute():
        review_path = root / review_path
    if not review_path.exists():
        print(f"cannot advance: missing review {review_path}")
        return 2

    text = review_path.read_text(encoding="utf-8")
    metadata = extract_metadata_block(text)
    if metadata is None:
        return metadata_error("missing required yaml metadata block")

    _, metadata_errors = validate_advance_metadata(metadata)

    try:
        state = load_json(current_phase_path(root))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"cannot advance: invalid current phase state: {exc}")
        return 2

    state_errors = validate_advance_state(state)
    errors = metadata_errors + state_errors
    if errors:
        for error in errors:
            print(f"cannot advance: {error}")
        return 1

    print(f"can advance: verdict {metadata['verdict'].upper()} and all safety gates are clear")
    return 0


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", help="Framework or target repository root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Print current phase status")
    add_root_argument(status)

    validate = subparsers.add_parser("validate", help="Validate framework files and state")
    validate.add_argument("--profile", choices=["auto", "framework", "target"], default="auto")
    add_root_argument(validate)

    can_advance = subparsers.add_parser("can-advance", help="Check whether a review allows advancement")
    can_advance.add_argument("--review", required=True, help="Path to phase review markdown")
    add_root_argument(can_advance)

    args = parser.parse_args(argv)
    root = project_root(getattr(args, "root", None))

    if args.command == "status":
        return cmd_status(root)
    if args.command == "validate":
        return cmd_validate(root, args.profile)
    if args.command == "can-advance":
        return cmd_can_advance(root, Path(args.review))
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
