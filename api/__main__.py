from __future__ import annotations

import argparse
import json

from api.backends import build_scoring_backend
from cps.data.manifest import load_manifest
from cps.runtime.config import load_phase1_context

from api.settings import DEFAULT_API_PROFILE, format_phase1_env_overrides, list_api_profiles


def _probe_phase1_logprobs(*, env_path: str | None, model_role: str, question_id: str | None) -> int:
    context = load_phase1_context(
        phase1_config_path="phase1.yaml",
        run_plan_path="configs/runs/smoke.json",
        env_path=env_path,
    )
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = next((item for item in bundle.sample if item.question_id == question_id), bundle.sample[0])
    backend = build_scoring_backend(context=context, backend_name="live", model_role=model_role)
    request_payload = backend.build_request_payload(
        question_text=question.question_text,
        answer_text=question.answer_text,
        ordered_paragraphs=(),
    )

    try:
        score = backend.score_answer(
            question_text=question.question_text,
            answer_text=question.answer_text,
            ordered_paragraphs=(),
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "red",
                    "profile": context.provider.profile_name,
                    "provider": context.provider.name,
                    "model_role": model_role,
                    "model_id": backend.model_id,
                    "question_id": question.question_id,
                    "base_url": context.provider.base_url,
                    "request_contract": {
                        "logprobs": request_payload["logprobs"],
                        "top_logprobs": request_payload["top_logprobs"],
                        "stream": request_payload["stream"],
                        "n": request_payload["n"],
                    },
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    nonzero_token_count = sum(1 for value in score.token_logprobs if abs(value) > 1e-12)
    print(
        json.dumps(
            {
                "status": "green",
                "profile": context.provider.profile_name,
                "provider": context.provider.name,
                "model_role": model_role,
                "model_id": backend.model_id,
                "question_id": question.question_id,
                "base_url": context.provider.base_url,
                "request_contract": {
                    "logprobs": request_payload["logprobs"],
                    "top_logprobs": request_payload["top_logprobs"],
                    "stream": request_payload["stream"],
                    "n": request_payload["n"],
                },
                "response_status": score.response_status,
                "token_count": len(score.token_logprobs),
                "nonzero_token_count": nonzero_token_count,
                "logprob_sum": score.logprob_sum,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Phase 1 API profile settings.")
    parser.add_argument(
        "--profile",
        default=DEFAULT_API_PROFILE,
        help="API profile used when printing runtime override settings.",
    )
    parser.add_argument(
        "--show-profiles",
        action="store_true",
        help="List available API provider profiles.",
    )
    parser.add_argument(
        "--export-phase1-env",
        action="store_true",
        help="Print shell-style runtime API overrides for the selected profile.",
    )
    parser.add_argument(
        "--probe-phase1-logprobs",
        action="store_true",
        help="Run a single live Phase 1 logprob probe and fail fast on degenerate token logprobs.",
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Optional env file used by the live Phase 1 logprob probe.",
    )
    parser.add_argument(
        "--model-role",
        choices=("small", "frontier"),
        default="small",
        help="Model role used by the live Phase 1 logprob probe.",
    )
    parser.add_argument(
        "--question-id",
        default=None,
        help="Optional question id used by the live Phase 1 logprob probe.",
    )
    args = parser.parse_args()

    handled = False
    if args.show_profiles:
        print("Available API profiles:")
        for profile in list_api_profiles():
            print(f"  - {profile.profile_name}")
            print(f"    provider: {profile.provider_name}")
            print(f"    default_base_url: {profile.default_base_url}")
            print(f"    phase1_logprob_ready: {profile.phase1_logprob_ready}")
            print(f"    note: {profile.note}")
        print("")
        handled = True

    if args.export_phase1_env:
        print(format_phase1_env_overrides(args.profile))
        handled = True

    if args.probe_phase1_logprobs:
        return _probe_phase1_logprobs(
            env_path=args.env,
            model_role=args.model_role,
            question_id=args.question_id,
        )

    if not handled:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
