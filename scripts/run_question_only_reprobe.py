from __future__ import annotations

import argparse
import json
from pathlib import Path

from cps.analysis.exports import write_json
from cps.analysis.reprobe import run_question_only_reprobe


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a single question-only contamination reprobe using the current Phase 1 backend and model-role resolution."
    )
    parser.add_argument(
        "--question-text",
        required=True,
        help="Question text used for the question-only reprobe.",
    )
    parser.add_argument(
        "--answer-text",
        required=True,
        help="Reference answer used for forced-decode replay scoring.",
    )
    parser.add_argument(
        "--question-id",
        default=None,
        help="Optional question id for bookkeeping.",
    )
    parser.add_argument(
        "--backend",
        choices=("mock", "live"),
        default="live",
        help="Backend used for reprobe execution.",
    )
    parser.add_argument(
        "--model-role",
        choices=("small", "frontier"),
        default="frontier",
        help="Model role used for reprobe execution.",
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Optional env file used to resolve provider credentials and overrides.",
    )
    parser.add_argument(
        "--phase1-config",
        default="phase1.yaml",
        help="Phase 1 config path used to resolve runtime context.",
    )
    parser.add_argument(
        "--run-plan",
        default="configs/runs/smoke.json",
        help="Run-plan path used to resolve storage/runtime defaults.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the full reprobe payload as JSON.",
    )
    args = parser.parse_args()

    try:
        payload = run_question_only_reprobe(
            question_text=args.question_text,
            answer_text=args.answer_text,
            question_id=args.question_id,
            backend_name=args.backend,
            model_role=args.model_role,
            env_path=args.env,
            phase1_config_path=args.phase1_config,
            run_plan_path=args.run_plan,
        )
    except Exception as exc:
        failure_payload = {
            "status": "red",
            "mode": "question_only_reprobe",
            "question_id": args.question_id or "",
            "backend": args.backend,
            "model_role": args.model_role,
            "error": str(exc),
        }
        if args.json_out:
            write_json(Path(args.json_out), failure_payload)
        print(json.dumps(failure_payload, ensure_ascii=False, indent=2))
        return 1

    if args.json_out:
        write_json(Path(args.json_out), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
