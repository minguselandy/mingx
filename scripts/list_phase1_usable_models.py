from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.model_probe import format_probe_markdown, probe_visible_models


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List models visible to the current OpenAI-compatible provider and probe which ones are usable for the current Phase 1 logprob contract.",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Env file used to resolve base_url and api_key.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Optional API profile override.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Per-model probe timeout in seconds.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the full JSON probe payload.",
    )
    parser.add_argument(
        "--markdown-out",
        default=None,
        help="Optional path to write a Markdown summary listing usable models.",
    )
    args = parser.parse_args()

    payload = probe_visible_models(
        env_path=args.env,
        profile_name=args.profile,
        timeout=args.timeout,
    )
    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        markdown_path = Path(args.markdown_out)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        command = (
            f"python scripts/list_phase1_usable_models.py --env {args.env}"
            f" --timeout {args.timeout}"
        )
        if args.profile:
            command += f" --profile {args.profile}"
        if args.json_out:
            command += f" --json-out {args.json_out}"
        command += f" --markdown-out {args.markdown_out}"
        markdown_path.write_text(
            format_probe_markdown(
                payload,
                command=command,
                json_report_path=args.json_out,
            ),
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
