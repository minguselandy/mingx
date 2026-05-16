from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from cps.benchmarks.fever_adapter import build_fever_candidate_pools
from cps.benchmarks.hotpot_adapter import HOTPOTQA_DATASET
from cps.benchmarks.hotpot_adapter import build_hotpot_candidate_pools
from cps.benchmarks.schemas import write_json
from cps.benchmarks.schemas import write_jsonl

FEVER_DATASET = "FEVER"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P61R public benchmark candidate pools.")
    parser.add_argument("--dataset", required=True, choices=[FEVER_DATASET, HOTPOTQA_DATASET])
    parser.add_argument("--claims-jsonl", required=True)
    parser.add_argument("--candidates-jsonl")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output-jsonl")
    parser.add_argument("--report-json")
    parser.add_argument("--blocked-report-json")
    args = parser.parse_args(argv)

    if args.dataset == HOTPOTQA_DATASET:
        result = build_hotpot_candidate_pools(
            input_json=args.claims_jsonl,
            split=args.split,
            limit=args.limit,
        )
    else:
        result = build_fever_candidate_pools(
            claims_jsonl=args.claims_jsonl,
            candidates_jsonl=args.candidates_jsonl,
            split=args.split,
            limit=args.limit,
        )

    if result.instances and args.output_jsonl:
        write_jsonl(Path(args.output_jsonl), result.instances)
    if args.report_json:
        write_json(Path(args.report_json), result.report)
    if result.blocked_report is not None and args.blocked_report_json:
        write_json(Path(args.blocked_report_json), result.blocked_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
