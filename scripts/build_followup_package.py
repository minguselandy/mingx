from __future__ import annotations

import argparse
import json
from pathlib import Path

from cps.analysis.exports import write_json
from cps.runtime.followup import build_followup_package


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a ready-to-run follow-up package from an approved drop list and replacement manifest."
    )
    parser.add_argument(
        "--source-plan",
        required=True,
        help="Source run-plan JSON used for the failed or reviewed batch.",
    )
    parser.add_argument(
        "--replacement-manifest",
        required=True,
        help="Replacement manifest JSON containing the approved drop ids and next same-hop selections.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Directory where the follow-up package will be written.",
    )
    parser.add_argument(
        "--decision-sheet",
        default=None,
        help="Optional operator decision sheet used for lineage plus approval-state validation.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional JSON path for the package summary payload.",
    )
    args = parser.parse_args()

    payload = build_followup_package(
        source_plan_path=args.source_plan,
        replacement_manifest_path=args.replacement_manifest,
        output_root=args.output_root,
        decision_sheet_path=args.decision_sheet,
    )
    if args.json_out:
        write_json(Path(args.json_out), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
