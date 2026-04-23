from __future__ import annotations

import argparse
import json

from cps.analysis.contamination_review import (
    build_contamination_review_packet,
    write_contamination_review_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export a human-in-the-loop review packet for questions that failed the "
            "Phase 1 contamination gate."
        )
    )
    parser.add_argument(
        "--run-summary",
        default=None,
        help="Optional run_summary.json path. If provided, contamination/calibration paths are resolved from it.",
    )
    parser.add_argument(
        "--contamination-report",
        default=None,
        help="Optional contamination_diagnostics.json path.",
    )
    parser.add_argument(
        "--calibration-manifest",
        default=None,
        help="Optional calibration_manifest.json path.",
    )
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=280,
        help="Character budget for each supporting paragraph excerpt in the review packet.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write the full JSON review packet.",
    )
    parser.add_argument(
        "--markdown-out",
        default=None,
        help="Optional path to write a Markdown prompt pack for manual AI review.",
    )
    args = parser.parse_args()

    payload = build_contamination_review_packet(
        run_summary_path=args.run_summary,
        contamination_report_path=args.contamination_report,
        calibration_manifest_path=args.calibration_manifest,
        snippet_chars=args.snippet_chars,
    )
    command_parts = ["python scripts/export_contamination_review_packet.py"]
    if args.run_summary:
        command_parts.extend(["--run-summary", args.run_summary])
    if args.contamination_report:
        command_parts.extend(["--contamination-report", args.contamination_report])
    if args.calibration_manifest:
        command_parts.extend(["--calibration-manifest", args.calibration_manifest])
    command_parts.extend(["--snippet-chars", str(args.snippet_chars)])
    if args.json_out:
        command_parts.extend(["--json-out", args.json_out])
    if args.markdown_out:
        command_parts.extend(["--markdown-out", args.markdown_out])
    write_contamination_review_outputs(
        payload=payload,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        command=" ".join(command_parts),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
