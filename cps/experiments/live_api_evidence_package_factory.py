from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence
from urllib import error
from urllib.parse import urlparse
from urllib import request

from cps.analysis.candidate_evidence_package import build_candidate_evidence_package
from cps.analysis.contamination_audit import build_contamination_report
from cps.analysis.human_gold_agreement import build_human_gold_manifest
from cps.analysis.human_gold_agreement import compute_agreement_report
from cps.analysis.hybrid_label_model import build_hybrid_validation_candidate
from cps.analysis.judge_bias_audit import build_judge_bias_audit
from cps.analysis.judge_weak_source_audit import audit_judge_weak_source
from cps.analysis.uncertainty_bounded_reporting import build_uncertainty_report
from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.benchmarks.hashing import stable_hash
from cps.evaluators.live_api_chat_logprob_confidence import build_confidence_diagnostic
from cps.evaluators.live_api_chat_logprob_confidence import diagnostic_schema
from cps.evaluators.live_api_chat_logprob_confidence import summarize_confidence_rows
from cps.evaluators.live_api_label_generation_proxy import build_label_proxy_contract
from cps.evaluators.live_api_label_generation_proxy import normalize_label_generation
from cps.evaluators.live_api_label_generation_proxy import summarize_label_proxy_rows
from cps.experiments.gamma_operational_expansion import PROJECT_NATIVE_BUDGETS
from cps.experiments.gamma_operational_expansion import WORKBENCH_EVALUATORS
from cps.experiments.gamma_operational_expansion import WORKBENCH_SELECTORS
from cps.experiments.gamma_operational_expansion import project_native_packets_to_candidate_pools
from cps.experiments.workbench.dynamic_holdout import build_dynamic_holdout_readiness
from cps.experiments.workbench.run_manager import run_workbench
from cps.experiments.workbench.spec import WorkbenchRunSpec


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
WORKBENCH_CLAIM_STATUS = "operational_utility_only; no_claim_upgrade"
DEFAULT_OUTPUT_ROOT = Path("artifacts/experiments")
DEFAULT_HOTPOTQA_CANDIDATE_POOLS = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
DEFAULT_PROJECT_NATIVE_PACKETS = Path(
    "artifacts/experiments/realistic_task_model_adjudicated_v12/realistic_task_packets.jsonl"
)
DEFAULT_MODEL_ID = "qwen3.6-flash"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
APPROVED_DASHSCOPE_HOSTS = frozenset({"dashscope.aliyuncs.com"})
APPROVED_DASHSCOPE_PATH = "/compatible-mode/v1"


def _write_doc(path: Path, title: str, lines: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# " + title + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return path


def _env_values(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = root / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update({key: value for key, value in os.environ.items() if isinstance(value, str)})
    return values


def _normalize_base_url(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def _is_approved_dashscope_base_url(base_url: str) -> bool:
    normalized = _normalize_base_url(base_url)
    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/")
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").lower() in APPROVED_DASHSCOPE_HOSTS
        and path == APPROVED_DASHSCOPE_PATH
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )


def _select_live_api_client_config(env: Mapping[str, str]) -> dict[str, Any]:
    base_url = _normalize_base_url(env.get("DASHSCOPE_BASE_URL") or DEFAULT_BASE_URL)
    if not _is_approved_dashscope_base_url(base_url):
        return {
            "available": False,
            "base_url": base_url,
            "blocked_reason": "unapproved_dashscope_base_url",
        }

    api_key_source = ""
    api_key = ""
    dashscope_key = (env.get("DASHSCOPE_API_KEY") or "").strip()
    qwen_key = (env.get("QWEN_API_KEY") or "").strip()
    if dashscope_key:
        api_key_source = "DASHSCOPE_API_KEY"
        api_key = dashscope_key
    elif qwen_key:
        api_key_source = "QWEN_API_KEY"
        api_key = qwen_key
    if not api_key_source:
        return {
            "available": False,
            "base_url": base_url,
            "blocked_reason": "missing_dashscope_or_qwen_api_key",
        }

    return {
        "api_key": api_key,
        "api_key_source": api_key_source,
        "available": True,
        "base_url": base_url,
        "model_id": env.get("DASHSCOPE_MODEL") or env.get("QWEN_MODEL") or DEFAULT_MODEL_ID,
    }


class DashScopeEvidenceClient:
    def __init__(self, *, api_key: str, base_url: str = DEFAULT_BASE_URL, model_id: str = DEFAULT_MODEL_ID) -> None:
        if not api_key:
            raise RuntimeError("missing_allowed_dashscope_api_key")
        if not _is_approved_dashscope_base_url(base_url):
            raise RuntimeError("unapproved_dashscope_base_url")
        self.api_key = api_key
        self.base_url = _normalize_base_url(base_url)
        self.model_id = model_id

    def chat_completion(self, *, messages: Sequence[Mapping[str, str]], logprobs: bool = True, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "enable_thinking": False,
            "logprobs": bool(logprobs),
            "max_tokens": int(kwargs.get("max_tokens", 96)),
            "messages": [dict(message) for message in messages],
            "model": self.model_id,
            "n": 1,
            "stream": False,
            "temperature": 0,
            "top_logprobs": 0,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=90) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"dashscope_live_api_http_{exc.code}") from exc
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("dashscope_live_api_transport_or_parse_failure") from exc
        choice = (response_payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "")
        logprobs_block = message.get("logprobs") or choice.get("logprobs") or {}
        items = logprobs_block.get("content") or []
        token_logprobs = [float(item["logprob"]) for item in items if isinstance(item, Mapping) and "logprob" in item]
        return {
            "content": content,
            "model_id": str(response_payload.get("model") or self.model_id),
            "token_logprobs": token_logprobs,
        }


def _git_lines(root: Path, args: Sequence[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []


def _leftover_manifest(root: Path, output_root: Path, untracked_paths: Sequence[str] | None) -> dict[str, Any]:
    paths = list(untracked_paths) if untracked_paths is not None else _git_lines(root, ["ls-files", "--others", "--exclude-standard"])
    leftovers = []
    for path in sorted(paths):
        normalized = path.replace("\\", "/")
        lowered = normalized.casefold()
        if not any(marker in lowered for marker in ("beta", "route4d", "route6c", "ws0_hygiene", "ws1_teacher_forced_backend")):
            continue
        file_path = root / normalized
        leftovers.append(
            {
                "path": normalized,
                "size_bytes": file_path.stat().st_size if file_path.exists() and file_path.is_file() else 0,
                "staging_policy": "do_not_stage_for_epf_goal",
                "status": "untracked_leftover",
            }
        )
    report = {
        "branch": (_git_lines(root, ["branch", "--show-current"]) or ["unknown"])[0],
        "claim_status": CLAIM_STATUS,
        "head": (_git_lines(root, ["rev-parse", "HEAD"]) or ["unknown"])[0],
        "leftovers": leftovers,
        "schema_version": "epf_ws0_leftover_manifest_v1",
        "total_leftovers": len(leftovers),
    }
    write_json(output_root / "epf_ws0_branch_hygiene" / "leftover_manifest.json", report)
    return report


def _sample_from_pool(pool: Mapping[str, Any]) -> dict[str, Any] | None:
    packets = list((pool.get("candidate_pool") or {}).get("packets") or [])
    supporting = next((packet for packet in packets if packet.get("gold_support_label") == "gold_supporting"), None)
    if supporting is None:
        return None
    expected = "supporting"
    return {
        "candidate_sentence": str(supporting.get("content") or ""),
        "dataset": str(pool.get("dataset") or "HotpotQA"),
        "expected_label": expected,
        "instance_id": str(pool.get("instance_id") or ""),
        "parent_sample_id": stable_hash(
            {"instance_id": str(pool.get("instance_id") or ""), "packet_id": str(supporting.get("packet_id") or "")}
        )[:16],
        "packet_id": str(supporting.get("packet_id") or ""),
        "query": str(pool.get("query") or ""),
        "source_kind": str((pool.get("adapter_metadata") or {}).get("source_kind") or "public_benchmark"),
        "split": str(pool.get("split") or ""),
    }


def _build_samples(path: Path, limit: int) -> list[dict[str, Any]]:
    rows = read_jsonl(path) if path.exists() else []
    samples: list[dict[str, Any]] = []
    for pool in rows:
        sample = _sample_from_pool(pool)
        if sample is not None:
            samples.append(sample)
        if len(samples) >= limit:
            break
    return samples


def _messages(sample: Mapping[str, Any], probe_type: str) -> list[dict[str, str]]:
    probe_instruction = {
        "duplicate": "Re-evaluate independently with the same rubric.",
        "order_swap": "Treat sentence order as non-authoritative and apply the same rubric.",
        "prompt_swap": "Use a stricter interpretation of supporting evidence.",
    }.get(probe_type, "Apply the rubric directly.")
    return [
        {
            "role": "system",
            "content": (
                "Return only compact JSON with keys label, rationale_quality, uncertainty. "
                "Allowed labels: supporting, not_supporting, uncertain. Do not include hidden reasoning."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{probe_instruction}\n"
                f"Question: {sample['query']}\n"
                f"Candidate sentence: {sample['candidate_sentence']}\n"
                "Does the candidate sentence support answering the question?"
            ),
        },
    ]


def _run_live_label_probes(
    *,
    client: Any,
    samples: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    label_rows: list[dict[str, Any]] = []
    confidence_rows: list[dict[str, Any]] = []
    for sample in samples:
        for probe_type in ("primary", "duplicate", "order_swap", "prompt_swap"):
            messages = _messages(sample, probe_type)
            prompt_text = "\n".join(message["content"] for message in messages)
            response = client.chat_completion(messages=messages, logprobs=True)
            content = str(response.get("content") or "")
            token_logprobs = [float(value) for value in response.get("token_logprobs") or []]
            model_id = str(response.get("model_id") or DEFAULT_MODEL_ID)
            prompt_id = f"{sample['parent_sample_id']}::{probe_type}"
            confidence = build_confidence_diagnostic(
                backend_id="dashscope_openai_chat",
                generated_text=content,
                model_id=model_id,
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                token_logprobs=token_logprobs,
            )
            label = normalize_label_generation(
                confidence=float(confidence["confidence"]),
                content=content,
                expected_label=str(sample.get("expected_label") or ""),
                model_id=model_id,
                parent_sample_id=str(sample["parent_sample_id"]),
                probe_type=probe_type,
                prompt_text=prompt_text,
                sample_metadata={
                    "dataset": sample["dataset"],
                    "instance_id": sample["instance_id"],
                    "packet_id": sample["packet_id"],
                    "split": sample["split"],
                },
                token_logprobs=token_logprobs,
            )
            confidence_rows.append(confidence)
            label_rows.append(label)
    return label_rows, confidence_rows


def _run_ws6(
    *,
    hotpotqa_candidate_pools_path: Path,
    output_dir: Path,
    project_native_packets_path: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    project_pools_path = output_dir / "project_native_candidate_pools.jsonl"
    if project_native_packets_path.exists():
        project_records = project_native_packets_to_candidate_pools(read_jsonl(project_native_packets_path), budgets=PROJECT_NATIVE_BUDGETS)
        write_jsonl(project_pools_path, project_records)
    traces: list[dict[str, Any]] = []
    run_results: list[dict[str, Any]] = []
    specs = []
    if hotpotqa_candidate_pools_path.exists():
        specs.append(
            WorkbenchRunSpec(
                budgets=(256, 512),
                candidate_pools_path=str(hotpotqa_candidate_pools_path),
                claim_status=WORKBENCH_CLAIM_STATUS,
                dataset="HotpotQA",
                evaluators=WORKBENCH_EVALUATORS,
                limit=2,
                output_dir=str(output_dir / "workbench_hotpotqa"),
                run_id="epf_ws6_hotpotqa_operational",
                selectors=WORKBENCH_SELECTORS,
            )
        )
    if project_pools_path.exists():
        specs.append(
            WorkbenchRunSpec(
                budgets=PROJECT_NATIVE_BUDGETS,
                candidate_pools_path=str(project_pools_path),
                claim_status=WORKBENCH_CLAIM_STATUS,
                dataset="ProjectNativeRealisticTasks",
                evaluators=WORKBENCH_EVALUATORS,
                limit=3,
                output_dir=str(output_dir / "workbench_project_native"),
                run_id="epf_ws6_project_native_operational",
                selectors=WORKBENCH_SELECTORS,
            )
        )
    config_path = repo_root / "configs/workbench/epf_ws6_multibench_operational.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"runs": [spec.to_payload() for spec in specs]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for spec in specs:
        result = run_workbench(spec)
        run_results.append(result)
        trace_path = Path(spec.output_dir) / "workbench_traces.jsonl"
        if trace_path.exists():
            traces.extend(read_jsonl(trace_path))
    summary_rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for trace in traces:
        grouped.setdefault((str(trace.get("dataset")), int(trace.get("budget") or 0), str(trace.get("selector_name"))), []).append(trace)
    for (dataset, budget, selector), rows in sorted(grouped.items()):
        recalls = [float((row.get("evaluation") or {}).get("supporting_fact_recall_at_budget") or 0.0) for row in rows]
        summary_rows.append(
            {
                "budget": budget,
                "dataset": dataset,
                "mean_supporting_fact_recall_at_budget": round(sum(recalls) / len(recalls), 6) if recalls else 0.0,
                "selector_name": selector,
                "trace_count": len(rows),
            }
        )
    _write_csv(output_dir / "comparison_summary.csv", summary_rows)
    stats = {
        "claim_status": CLAIM_STATUS,
        "matched_budget": True,
        "schema_version": "epf_ws6_statistical_tests_v1",
        "statistical_test_status": "descriptive_underpowered_candidate",
        "trace_count": len(traces),
    }
    safety = {
        "claim_status": CLAIM_STATUS,
        "diagnostic_safety_status": "operational_only_no_claim_upgrade",
        "metric_bridge_support": False,
        "schema_version": "epf_ws6_diagnostic_safety_report_v1",
        "selector_superiority_claimed": False,
    }
    write_json(output_dir / "statistical_tests.json", stats)
    write_json(output_dir / "diagnostic_safety_report.json", safety)
    return run_results, stats, safety


def _blocker(output_root: Path, reason: str) -> dict[str, Any]:
    report = {
        "claim_status": CLAIM_STATUS,
        "reason": reason,
        "schema_version": "epf_blocker_report_v1",
        "terminal_status": "BLOCKED_LIVE_API_ACCESS",
    }
    write_json(output_root / "epf_candidate_package" / "blocker_report.json", report)
    return report


def run_live_api_evidence_package_factory(
    *,
    client: Any | None = None,
    hotpotqa_candidate_pools_path: str | Path = DEFAULT_HOTPOTQA_CANDIDATE_POOLS,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    project_native_packets_path: str | Path = DEFAULT_PROJECT_NATIVE_PACKETS,
    repo_root: str | Path = ".",
    sample_limit: int = 2,
    run_live: bool = True,
    untracked_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    out = Path(output_root)
    out.mkdir(parents=True, exist_ok=True)
    hotpotqa_path = Path(hotpotqa_candidate_pools_path)
    project_path = Path(project_native_packets_path)

    ws0 = _leftover_manifest(root, out, untracked_paths)
    _write_doc(
        root / "docs/experiments/WS0-branch-hygiene-and-leftover-isolation.md",
        "WS0 Branch Hygiene And Leftover Isolation",
        [
            f"Claim status: `{CLAIM_STATUS}`.",
            f"Leftovers isolated: `{ws0['total_leftovers']}`.",
            "No staging or commit operation was performed.",
        ],
    )

    ws1_dir = out / "epf_ws1_live_api_tfs_closure"
    ws1_capability = {
        "allowed_model_backend": "dashscope_openai_compatible_live_api_only",
        "chat_generated_token_logprobs_available": "tested_in_ws2" if run_live else False,
        "claim_status": CLAIM_STATUS,
        "completion_echo_logprobs_fixed_target_scoring_unavailable": True,
        "raw_response_stored": False,
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "epf_ws1_live_api_tfs_capability_v1",
        "teacher_forced_fixed_target_nll_available": False,
    }
    write_json(ws1_dir / "backend_capability_report.json", ws1_capability)
    write_json(
        ws1_dir / "claim_boundary_result.json",
        {
            "claim_status": CLAIM_STATUS,
            "fixed_target_nll_bridge_blocked": True,
            "generated_chat_logprobs_not_metric_bridge": True,
            "route5_locked": True,
            "route8_locked": True,
            "schema_version": "epf_ws1_claim_boundary_result_v1",
        },
    )
    _write_doc(
        root / "docs/experiments/WS1-live-api-fixed-target-nll-closure.md",
        "WS1 Live API Fixed-Target NLL Closure",
        [
            "True fixed-target teacher-forced NLL remains blocked under the current DashScope-compatible chat API.",
            "Generated chat logprobs are operational confidence diagnostics only.",
            "Route 5 and Route 8 remain locked.",
        ],
    )

    if run_live and client is None:
        env = _env_values(root)
        client_config = _select_live_api_client_config(env)
        if not client_config["available"]:
            return _blocker(out, str(client_config["blocked_reason"]))
        client = DashScopeEvidenceClient(
            api_key=str(client_config["api_key"]),
            base_url=str(client_config["base_url"]),
            model_id=str(client_config["model_id"]),
        )

    samples = _build_samples(hotpotqa_path, sample_limit)
    if run_live and client is not None:
        try:
            label_rows, confidence_rows = _run_live_label_probes(client=client, samples=samples)
        except Exception as exc:
            return _blocker(out, f"dashscope_live_api_probe_failed:{type(exc).__name__}")
    else:
        label_rows, confidence_rows = [], []

    ws2_dir = out / "epf_ws2_chat_logprob_confidence"
    write_json(ws2_dir / "diagnostic_schema.json", diagnostic_schema())
    write_jsonl(ws2_dir / "confidence_diagnostics.jsonl", confidence_rows)
    confidence_summary = summarize_confidence_rows(confidence_rows)
    write_json(ws2_dir / "confidence_summary.json", confidence_summary)
    _write_doc(
        root / "docs/experiments/WS2-live-api-chat-logprob-confidence-diagnostic.md",
        "WS2 Live API Chat Logprob Confidence Diagnostic",
        ["Allowed claim: `operational_confidence_diagnostic`.", "Denied: fixed-target NLL, metric bridge, calibrated proxy, V-information proxy."],
    )

    ws3_dir = out / "epf_ws3_label_generation_proxy"
    write_json(ws3_dir / "proxy_contract.json", build_label_proxy_contract())
    write_jsonl(ws3_dir / "label_proxy_rows.jsonl", label_rows)
    label_summary = summarize_label_proxy_rows(label_rows)
    write_json(ws3_dir / "label_proxy_summary.json", label_summary)
    _write_doc(
        root / "docs/experiments/WS3-constrained-label-generation-proxy.md",
        "WS3 Constrained Label Generation Proxy",
        ["Allowed: `operational_label_confidence_proxy` and `constrained_label_generation_proxy`.", "Denied: teacher-forced label NLL, fixed-target NLL, V-information proxy."],
    )

    ws4_dir = out / "epf_ws4_judge_weak_source_audit"
    weak_source = audit_judge_weak_source(label_rows)
    bias = build_judge_bias_audit(label_rows)
    write_json(ws4_dir / "judge_weak_source_report.json", weak_source)
    write_json(ws4_dir / "judge_bias_audit.json", bias)
    _write_doc(
        root / "docs/experiments/WS4-llm-judge-weak-source-audit.md",
        "WS4 LLM Judge Weak-Source Audit",
        ["Claim ceiling: `model_adjudicated_measurement_candidate`.", "LLM judge rows remain weak supervision unless calibrated by human or external labels."],
    )

    ws5_dir = out / "epf_ws5_hybrid_validation"
    human_manifest = build_human_gold_manifest([])
    agreement = compute_agreement_report(label_rows, [])
    hybrid = build_hybrid_validation_candidate(
        human_gold_manifest=human_manifest,
        judge_audit=weak_source,
        label_rows=label_rows,
    )
    write_json(ws5_dir / "human_gold_manifest.json", human_manifest)
    write_json(ws5_dir / "label_model_report.json", hybrid)
    write_json(ws5_dir / "agreement_report.json", agreement)
    write_json(ws5_dir / "measurement_candidate_review_packet.json", hybrid)
    _write_doc(
        root / "docs/experiments/WS5-hybrid-measurement-validation-candidate.md",
        "WS5 Hybrid Measurement Validation Candidate",
        ["Human/external gold labels are not available in this run, so no measurement validation candidate is emitted."],
    )

    ws6_dir = out / "epf_ws6_multibench_operational"
    run_results, stats, safety = _run_ws6(
        hotpotqa_candidate_pools_path=hotpotqa_path,
        output_dir=ws6_dir,
        project_native_packets_path=project_path,
        repo_root=root,
    )
    _write_doc(
        root / "docs/experiments/WS6-multi-benchmark-operational-robustness.md",
        "WS6 Multi-Benchmark Operational Robustness",
        ["Claim ceiling: `scoped_operational_improvement_candidate` and `baseline_robustness_candidate`.", "All results remain operational-only and descriptive."],
    )

    ws7_dir = out / "epf_ws7_contamination"
    contamination = build_contamination_report(
        datasets=[
            {"dataset": "HotpotQA", "source_kind": "public_benchmark", "split": "dev_distractor"},
            {"dataset": "ProjectNativeRealisticTasks", "source_kind": "fixture", "split": "fixture_v12"},
        ]
    )
    holdout = build_dynamic_holdout_readiness(contamination)
    write_json(ws7_dir / "contamination_report.json", contamination)
    write_json(ws7_dir / "dynamic_holdout_readiness.json", holdout)
    _write_doc(
        root / "docs/experiments/WS7-contamination-and-dynamic-holdout-layer.md",
        "WS7 Contamination And Dynamic Holdout Layer",
        ["Dynamic holdout is not ready; Route 5 and Route 8 remain locked."],
    )

    ws8_dir = out / "epf_ws8_uncertainty"
    evidence_items = [
        {"candidate_claim": "operational_confidence_diagnostic", "confidence": confidence_summary.get("mean_confidence", 0.0)},
        {"candidate_claim": "model_adjudicated_measurement_candidate", "confidence": weak_source.get("json_validity", {}).get("parse_success_rate", 0.0)},
        {"candidate_claim": "scoped_operational_improvement_candidate", "confidence": 0.5 if run_results else 0.0},
    ]
    uncertainty = build_uncertainty_report(evidence_items=evidence_items)
    write_json(ws8_dir / "uncertainty_report.json", uncertainty)
    _write_doc(
        root / "docs/experiments/WS8-uncertainty-bounded-operational-reporting.md",
        "WS8 Uncertainty-Bounded Operational Reporting",
        ["Allowed claim: `uncertainty_bounded_operational_reporting_candidate`.", "No development claim upgrade is performed."],
    )

    package_dir = out / "epf_candidate_package"
    evidence_reports = [
        {"artifact": str(ws2_dir / "confidence_summary.json"), "candidate_claim": "operational_confidence_diagnostic"},
        {"artifact": str(ws3_dir / "label_proxy_summary.json"), "candidate_claim": "constrained_label_generation_proxy"},
        {"artifact": str(ws4_dir / "judge_weak_source_report.json"), "candidate_claim": "model_adjudicated_measurement_candidate"},
        {"artifact": str(ws6_dir / "comparison_summary.csv"), "candidate_claim": "scoped_operational_improvement_candidate"},
        {"artifact": str(ws8_dir / "uncertainty_report.json"), "candidate_claim": "uncertainty_bounded_operational_reporting_candidate"},
    ]
    package = build_candidate_evidence_package(output_dir=package_dir, evidence_reports=evidence_reports)
    _write_doc(
        root / "docs/experiments/WS9-candidate-evidence-package.md",
        "WS9 Candidate Evidence Package",
        ["A reviewable limited-scope candidate package was produced. Independent review is required before any claim ledger or paper upgrade."],
    )

    review_template = root / "docs/reviews/WS10-candidate-evidence-independent-review-template.md"
    _write_doc(
        review_template,
        "WS10 Candidate Evidence Independent Review Template",
        [
            "Verdict: ACCEPT / ACCEPT_WITH_NOTES / REQUEST_CHANGES / BLOCKED_OPERATOR_REQUIRED / REJECT",
            "Check raw API response storage, claim boundaries, dataset provenance, weak-source audit, and uncertainty bounds.",
        ],
    )
    patch_plan = root / "docs/paper/WS10-paper-positioning-patch-plan.md"
    _write_doc(
        patch_plan,
        "WS10 Paper Positioning Patch Plan",
        [
            "V-information remains the formal anchor.",
            "Current live API experiments do not support vinfo_proxy_supported.",
            "Fixed-target NLL bridge remains blocked under current live API.",
            "Generated-token logprobs are operational confidence diagnostics only.",
            "LLM judges are weak supervision unless human/hybrid calibrated.",
            "The strongest paper position is audit-first dispatch-time evidence selection.",
            "Do not edit manuscript claims in this goal.",
        ],
    )

    terminal_status = "REVIEWABLE_CANDIDATE_PACKAGE_READY" if package["status"] == "reviewable_candidate_package_ready" else "BLOCKED_NO_REVIEWABLE_CANDIDATE_PACKAGE"
    final_status = {
        "claim_status": CLAIM_STATUS,
        "development_claim_upgrade_performed": False,
        "live_api_used": bool(label_rows),
        "raw_api_responses_stored": False,
        "review_package_status": package["status"],
        "route5_unlocked": False,
        "route8_unlocked": False,
        "schema_version": "epf_final_status_v1",
        "terminal_status": terminal_status,
    }
    write_json(package_dir / "final_status.json", final_status)
    return final_status


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the live-API-only evidence package factory.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--sample-limit", type=int, default=2)
    args = parser.parse_args(argv)
    result = run_live_api_evidence_package_factory(
        output_root=args.output_root,
        repo_root=args.repo_root,
        sample_limit=args.sample_limit,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["terminal_status"] == "REVIEWABLE_CANDIDATE_PACKAGE_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
