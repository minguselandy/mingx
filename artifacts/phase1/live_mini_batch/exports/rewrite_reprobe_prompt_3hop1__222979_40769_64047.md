# Fresh Question-Only Reprobe Prompt

- Question ID: `3hop1__222979_40769_64047`
- Current status: `drop_and_replace`
- Current frontier model default: `qwen3.6-plus`
- Gate threshold: `baseline_logp <= log(0.5)` required for contamination clearance on the rewritten item
- Scope: operator-side reprobe packet for one controlled rewrite candidate

## Purpose

This packet is for a **fresh question-only reprobe** of the currently preferred
rewrite candidate for `3hop1__222979_40769_64047`.

It is intentionally narrow:

- one rewritten question
- question-only
- same gold answer
- no supporting paragraphs

This packet does **not** authorize automatic reuse of the rewritten question in
future runs. It only prepares a clean reprobe decision.

## Executed Result

This reprobe has now been executed live.

- backend: `live`
- model role: `frontier`
- model id: `qwen3.6-plus`
- response status: `200`
- baseline_logp: `-0.00028821608191265113`
- threshold_logp: `-0.6931471805599453`
- passes contamination threshold: `false`
- resulting disposition: `drop_and_replace`

## Recommended Rewrite Candidate

`When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?`

Gold answer:

`Sales began worldwide in April 2012`

## Advisory AI Review Prompt

Use this prompt only for a qualitative pre-screen. It is advisory and cannot
clear the contamination gate by itself.

```text
You are performing a contamination pre-screen for a rewritten MuSiQue-style question.

Rules:
- Question-only review.
- Do not use hidden gold-answer metadata beyond what is explicitly shown below.
- Judge whether a strong frontier language model could likely answer the question from prior knowledge alone.
- Return strict JSON with keys:
  "question_id", "judgement", "confidence", "primary_mechanism", "secondary_mechanisms", "reasoning", "keep_for_runtime_reprobe"
- Allowed judgement values: "likely_contaminated", "uncertain", "likely_clean"
- Allowed confidence values: "high", "medium", "low"
- Allowed primary_mechanism values: "direct_leakage", "near_unique_entity_chain", "memorized_public_fact", "question_collapse", "dataset_artifact", "unclear"
- "keep_for_runtime_reprobe" must be true or false

question_id: 3hop1__222979_40769_64047
rewritten_question: When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?
gold_answer_for_operator_reference_only: Sales began worldwide in April 2012
```

## Runtime Reprobe Spec

This is the actual decision rule that matters.

Run a fresh **question-only** baseline score under the current frontier model:

- model role: `frontier`
- model id: `qwen3.6-plus`
- context paragraphs: none
- question text:
  `When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?`
- forced-decode reference answer:
  `Sales began worldwide in April 2012`

Decision rule:

1. Compute `baseline_logp = log P(y* | q)` on the rewritten question with no paragraphs.
2. Compare it to `log(0.5)`.
3. If `baseline_logp > log(0.5)`, reject the rewrite and mark the item `drop_and_replace`.
4. If `baseline_logp <= log(0.5)`, the rewrite is eligible for human-reviewed lineage tracking and possible future reuse.

Recommended helper command:

```bash
python scripts/run_question_only_reprobe.py \
  --backend live \
  --model-role frontier \
  --env .env \
  --question-id 3hop1__222979_40769_64047 \
  --question-text "When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?" \
  --answer-text "Sales began worldwide in April 2012"
```

## Copy-Paste Runtime Probe Payload

Use this block when preparing a one-off reprobe request or internal helper:

```json
{
  "question_id": "3hop1__222979_40769_64047",
  "mode": "question_only_reprobe",
  "model_role": "frontier",
  "model_id": "qwen3.6-plus",
  "question_text": "When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?",
  "answer_text": "Sales began worldwide in April 2012",
  "ordered_paragraphs": []
}
```

## Human Recording Block

- Approved for reprobe: `yes`
- Reviewer: `[pending_manual_name]`
- Reprobe executed by: `runtime helper`
- Measured `baseline_logp`: `-0.00028821608191265113`
- Threshold comparison: `failed`
- Final disposition:
  - `drop_and_replace`

## Reminder

Passing this reprobe would only mean the rewritten item is worth considering for
future reuse.

It would still not:

- clear the contamination gate for the already completed reduced-scope run
- retroactively upgrade the current run to `measurement_validated`
- remove the need for human approval and lineage tracking
