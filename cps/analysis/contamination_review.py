from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Mapping

from cps.analysis.exports import write_json, write_text
from cps.data.manifest import ManifestQuestion, load_manifest


def _coerce_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def resolve_review_inputs(
    *,
    run_summary_path: str | Path | None = None,
    contamination_report_path: str | Path | None = None,
    calibration_manifest_path: str | Path | None = None,
) -> dict[str, Path]:
    resolved_run_summary_path = _coerce_path(run_summary_path)
    resolved_contamination_path = _coerce_path(contamination_report_path)
    resolved_calibration_path = _coerce_path(calibration_manifest_path)

    if resolved_run_summary_path is not None:
        run_summary = json.loads(resolved_run_summary_path.read_text(encoding="utf-8"))
        resolved_contamination_path = resolved_contamination_path or Path(
            str(run_summary["contamination"]["path"])
        ).expanduser().resolve()
        resolved_calibration_path = resolved_calibration_path or Path(
            str(run_summary["calibration_manifest_path"])
        ).expanduser().resolve()

    if resolved_contamination_path is None or resolved_calibration_path is None:
        raise ValueError(
            "Provide --run-summary or both --contamination-report and --calibration-manifest."
        )

    calibration_manifest = json.loads(resolved_calibration_path.read_text(encoding="utf-8"))
    source_manifest_path = Path(str(calibration_manifest["source_manifest_path"])).expanduser().resolve()

    return {
        "run_summary_path": resolved_run_summary_path,
        "contamination_report_path": resolved_contamination_path,
        "calibration_manifest_path": resolved_calibration_path,
        "source_manifest_path": source_manifest_path,
    }


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _alias_hits(question_text: str, aliases: tuple[str, ...]) -> list[str]:
    normalized_question = _normalized_text(question_text)
    hits: list[str] = []
    for alias in aliases:
        normalized_alias = _normalized_text(alias)
        if normalized_alias and normalized_alias in normalized_question:
            hits.append(alias)
    return hits


def _supporting_paragraph_rows(
    question: ManifestQuestion,
    *,
    snippet_chars: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for paragraph in question.paragraphs:
        if not paragraph.is_supporting:
            continue
        excerpt = paragraph.text[:snippet_chars].strip()
        if len(paragraph.text) > snippet_chars:
            excerpt += "..."
        rows.append(
            {
                "paragraph_id": paragraph.paragraph_id,
                "title": paragraph.title,
                "text_excerpt": excerpt,
            }
        )
    return rows


def _question_only_prompt(
    *,
    question_id: str,
    hop_depth: str,
    question_text: str,
) -> str:
    return "\n".join(
        [
            "You are auditing a MuSiQue-style question for contamination risk.",
            "Stage 1 is question-only: do not use any hidden answer, retrieval result, or external notes.",
            "Decide whether a strong frontier LM could likely answer this question from prior knowledge alone.",
            "Return strict JSON with keys:",
            '  "question_id", "judgement", "confidence", "primary_mechanism", "secondary_mechanisms", "reasoning", "rewrite_worth_trying"',
            'Allowed judgement values: "likely_contaminated", "uncertain", "likely_clean".',
            'Allowed confidence values: "high", "medium", "low".',
            'Allowed primary_mechanism values: "direct_leakage", "near_unique_entity_chain", "memorized_public_fact", "question_collapse", "dataset_artifact", "unclear".',
            "",
            f"question_id: {question_id}",
            f"hop_depth: {hop_depth}",
            f"question_text: {question_text}",
        ]
    )


def _rewrite_prompt(
    *,
    question_id: str,
    hop_depth: str,
    question_text: str,
    answer_text: str,
    supporting_paragraphs: list[dict[str, Any]],
) -> str:
    supporting_lines: list[str] = []
    for row in supporting_paragraphs:
        supporting_lines.append(
            f"- paragraph_id={row['paragraph_id']} | title={row['title']} | excerpt={row['text_excerpt']}"
        )
    if not supporting_lines:
        supporting_lines.append("- No supporting paragraphs were included in the packet.")
    return "\n".join(
        [
            "Stage 2 is rewrite planning.",
            "You may now inspect the gold answer and supporting evidence.",
            "Propose the smallest rewrite that reduces question-only answerability while preserving the same gold answer and hop structure.",
            "Do not introduce facts not supported by the evidence. Do not change the intended answer.",
            "Return strict JSON with keys:",
            '  "question_id", "rewrite_status", "contamination_cause", "rewrite_strategy", "rewritten_question", "answer_preserved", "hop_structure_preserved", "residual_risk", "operator_note"',
            'Allowed rewrite_status values: "rewrite_recommended", "drop_and_replace", "needs_human_only".',
            'Allowed residual_risk values: "high", "medium", "low".',
            "",
            f"question_id: {question_id}",
            f"hop_depth: {hop_depth}",
            f"original_question: {question_text}",
            f"gold_answer: {answer_text}",
            "supporting_evidence:",
            *supporting_lines,
        ]
    )


def _build_question_review_row(
    *,
    contamination_row: Mapping[str, Any],
    question: ManifestQuestion,
    threshold_logp: float,
    snippet_chars: int,
) -> dict[str, Any]:
    question_tokens = set(_tokenize(question.question_text))
    answer_tokens = set(_tokenize(question.answer_text))
    shared_tokens = sorted(token for token in question_tokens & answer_tokens if len(token) >= 3)
    answer_in_question = _normalized_text(question.answer_text) in _normalized_text(question.question_text)
    alias_hits = _alias_hits(question.question_text, question.answer_aliases)
    supporting_paragraphs = _supporting_paragraph_rows(question, snippet_chars=snippet_chars)
    baseline_logp = float(contamination_row["baseline_logp"])
    baseline_probability = math.exp(baseline_logp)

    return {
        "question_id": question.question_id,
        "hop_depth": question.hop_depth,
        "model_role": contamination_row.get("model_role"),
        "model_id": contamination_row.get("model_id"),
        "baseline_logp": baseline_logp,
        "baseline_probability": baseline_probability,
        "threshold_logp": threshold_logp,
        "threshold_probability": math.exp(threshold_logp),
        "logp_margin_vs_threshold": baseline_logp - threshold_logp,
        "probability_margin_vs_threshold": baseline_probability - math.exp(threshold_logp),
        "question_text": question.question_text,
        "answer_text": question.answer_text,
        "answer_aliases": list(question.answer_aliases),
        "paragraph_count": question.paragraph_count,
        "supporting_paragraphs": supporting_paragraphs,
        "heuristic_signals": {
            "answer_string_appears_in_question": answer_in_question,
            "answer_alias_hits_in_question": alias_hits,
            "shared_question_answer_tokens": shared_tokens,
            "question_char_length": len(question.question_text),
            "question_word_count": len(question.question_text.split()),
            "supporting_paragraph_count": len(supporting_paragraphs),
        },
        "stage1_question_only_prompt": _question_only_prompt(
            question_id=question.question_id,
            hop_depth=question.hop_depth,
            question_text=question.question_text,
        ),
        "stage2_rewrite_prompt": _rewrite_prompt(
            question_id=question.question_id,
            hop_depth=question.hop_depth,
            question_text=question.question_text,
            answer_text=question.answer_text,
            supporting_paragraphs=supporting_paragraphs,
        ),
    }


def build_contamination_review_packet(
    *,
    run_summary_path: str | Path | None = None,
    contamination_report_path: str | Path | None = None,
    calibration_manifest_path: str | Path | None = None,
    snippet_chars: int = 280,
) -> dict[str, Any]:
    resolved_paths = resolve_review_inputs(
        run_summary_path=run_summary_path,
        contamination_report_path=contamination_report_path,
        calibration_manifest_path=calibration_manifest_path,
    )
    contamination_payload = json.loads(
        resolved_paths["contamination_report_path"].read_text(encoding="utf-8")
    )
    source_bundle = load_manifest(resolved_paths["source_manifest_path"])
    by_question_id = {question.question_id: question for question in source_bundle.sample}
    threshold_logp = float(contamination_payload["threshold_logp"])

    review_rows: list[dict[str, Any]] = []
    for contamination_row in contamination_payload.get("baseline_rows") or []:
        if not contamination_row.get("above_threshold"):
            continue
        question_id = str(contamination_row["question_id"])
        question = by_question_id.get(question_id)
        if question is None:
            raise KeyError(f"Question {question_id} is missing from source manifest.")
        review_rows.append(
            _build_question_review_row(
                contamination_row=contamination_row,
                question=question,
                threshold_logp=threshold_logp,
                snippet_chars=snippet_chars,
            )
        )

    return {
        "status": "computed",
        "review_scope": "above_threshold_questions_only",
        "automation_policy": {
            "auto_clear_contamination_gate": False,
            "auto_rewrite_and_rerun": False,
            "human_signoff_required": True,
        },
        "source_paths": {
            "run_summary": (
                str(resolved_paths["run_summary_path"])
                if resolved_paths["run_summary_path"] is not None
                else ""
            ),
            "contamination_report": str(resolved_paths["contamination_report_path"]),
            "calibration_manifest": str(resolved_paths["calibration_manifest_path"]),
            "source_manifest": str(resolved_paths["source_manifest_path"]),
        },
        "threshold": {
            "logp": threshold_logp,
            "probability": math.exp(threshold_logp),
            "gate_decision": contamination_payload.get("gate_decision"),
        },
        "question_count": len(review_rows),
        "questions": review_rows,
    }


def format_contamination_review_markdown(
    payload: Mapping[str, Any],
    *,
    command: str | None = None,
    json_report_path: str | None = None,
) -> str:
    lines = [
        "# Phase 1 Contamination Review Packet",
        "",
        "- Purpose: support human-in-the-loop AI triage after a contamination gate failure.",
        f"- Review scope: `{payload.get('review_scope', '')}`",
        f"- Question count: `{payload.get('question_count', 0)}`",
        f"- Gate decision: `{payload.get('threshold', {}).get('gate_decision', '')}`",
        f"- Threshold logp: `{payload.get('threshold', {}).get('logp', '')}`",
        f"- Threshold probability: `{payload.get('threshold', {}).get('probability', '')}`",
    ]
    if command:
        lines.extend(
            [
                "",
                "## Regenerate",
                "",
                "```bash",
                command,
                "```",
            ]
        )
    if json_report_path:
        lines.extend(["", "## Full JSON Report", "", f"- `{json_report_path}`"])
    lines.extend(
        [
            "",
            "## Operator Rules",
            "",
            "- AI output is advisory only. It does not clear the contamination gate.",
            "- Do not auto-rerun the protocol from rewritten questions without recording lineage and human approval.",
            "- Prefer minimal rewrites. If the answer remains too recoverable from the question alone, drop and replace the item.",
        ]
    )
    for question in payload.get("questions") or []:
        lines.extend(
            [
                "",
                f"## {question['question_id']}",
                "",
                f"- Hop depth: `{question['hop_depth']}`",
                f"- Model: `{question['model_id']}` ({question['model_role']})",
                f"- Baseline logp: `{question['baseline_logp']}`",
                f"- Baseline probability: `{question['baseline_probability']}`",
                f"- Question: {question['question_text']}",
                f"- Gold answer: `{question['answer_text']}`",
                "",
                "### Heuristic Signals",
                "",
                f"- `answer_string_appears_in_question = {question['heuristic_signals']['answer_string_appears_in_question']}`",
                f"- `answer_alias_hits_in_question = {question['heuristic_signals']['answer_alias_hits_in_question']}`",
                f"- `shared_question_answer_tokens = {question['heuristic_signals']['shared_question_answer_tokens']}`",
                "",
                "### Supporting Paragraphs",
                "",
            ]
        )
        supporting_rows = question.get("supporting_paragraphs") or []
        if supporting_rows:
            for row in supporting_rows:
                lines.append(
                    f"- `paragraph_id={row['paragraph_id']}` | `{row['title']}` | {row['text_excerpt']}"
                )
        else:
            lines.append("- No supporting paragraphs were available.")
        lines.extend(
            [
                "",
                "### Stage 1 Prompt",
                "",
                "```text",
                str(question["stage1_question_only_prompt"]),
                "```",
                "",
                "### Stage 2 Prompt",
                "",
                "```text",
                str(question["stage2_rewrite_prompt"]),
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def write_contamination_review_outputs(
    *,
    payload: Mapping[str, Any],
    json_out: str | Path | None = None,
    markdown_out: str | Path | None = None,
    command: str | None = None,
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    if json_out is not None:
        path = write_json(Path(json_out), dict(payload))
        outputs["json"] = str(path)
    if markdown_out is not None:
        path = write_text(
            Path(markdown_out),
            format_contamination_review_markdown(
                payload,
                command=command,
                json_report_path=outputs.get("json"),
            ),
        )
        outputs["markdown"] = str(path)
    return outputs
