# Contamination Triage Memo

- Run: `phase1-cohort-20260423033750`
- Scope: `pilot_reduced_scope`
- Source packet: `contamination_review_packet.md`
- Memo status: operator-side advisory memo
- Gate status: `fail`
- Default repository action remains: `stop_and_escalate`

## Run-Level Conclusion

This run remains a scientific stop.

The engineering path succeeded far enough to materialize bridge outputs,
annotation exports, and contamination review artifacts, but the contamination
gate failed at `3/3` executed questions. This memo does not clear that gate.

My operator recommendation for this reduced-scope batch is:

1. Do not rerun from the current three questions as-is.
2. Treat all three questions as `drop_and_replace`.
3. Record the fourth-hop item as a likely upstream data-quality / entity-linking issue, not just a wording problem.

## Per-Question Decisions

| question_id | decision | primary mechanism | residual risk | operator note |
| --- | --- | --- | --- | --- |
| `2hop__86458_20273` | `drop_and_replace` | `memorized_public_fact` + `question_collapse` | high | The clue directly points to John Knox; the answer year is likely recoverable from prior knowledge alone. |
| `3hop1__222979_40769_64047` | `drop_and_replace` | `near_unique_entity_chain` + `question_collapse` | high | A controlled rewrite attempt was reprobed live and still failed the contamination threshold. |
| `4hop1__76111_624859_355213_203322` | `drop_and_replace` | `dataset_artifact` + `question_collapse` | high | The evidence path appears to rely on a Cleveland, Ohio / Cleveland, North Carolina collision and should not be trusted as a clean rewrite target. |

## Detailed Judgements

### 1. `2hop__86458_20273`

- Question: `In what year did the founder of the Presbyterian Church die?`
- Gold answer: `1572`
- Decision: `drop_and_replace`

Stage 1 judgement:

- `judgement = likely_contaminated`
- `confidence = high`
- `primary_mechanism = memorized_public_fact`
- `secondary_mechanisms = ["question_collapse", "near_unique_entity_chain"]`

Reasoning:

- `founder of the Presbyterian Church` is already a strong identifier for John Knox.
- A strong frontier LM can plausibly jump directly from that clue to the answer year without any need for the context paragraphs.
- The observed baseline probability is already near 1.0, which is too severe to treat as a mild wording issue.

Stage 2 decision:

- Minimal rewrite is not recommended as the primary path.
- Even if the wording is changed to indirect clues such as `the Scot who studied under Calvin in Geneva`, the answer path still collapses to a historically famous person with a memorized death year.

Operator note:

- Prefer replacing this item rather than spending more budget on rewrite-and-reprobe loops.

### 2. `3hop1__222979_40769_64047`

- Question: `When did the RX 350 from the Scion owner's luxury division change body style?`
- Gold answer: `Sales began worldwide in April 2012`
- Decision: `drop_and_replace`

Stage 1 judgement:

- `judgement = likely_contaminated`
- `confidence = medium`
- `primary_mechanism = near_unique_entity_chain`
- `secondary_mechanisms = ["question_collapse"]`

Reasoning:

- The clue bundle `RX 350` + `Scion owner` + `luxury division` narrows the target too aggressively.
- This looks more like a phrasing-level over-identification problem than a fundamental invalid question.
- Unlike the Presbyterian example, this item does not look like a universally famous public fact; it looks salvageable if the identifying chain is made less direct.

Stage 2 update:

- A controlled rewrite attempt was tested with a fresh live question-only reprobe.
- Rewritten question:
  `When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?`
- Live reprobe result:
  - `model_id = qwen3.6-plus`
  - `baseline_logp = -0.00028821608191265113`
  - `threshold_logp = -0.6931471805599453`
  - `passes_contamination_threshold = false`

Final operator conclusion:

- The rewrite path is no longer recommended for this item.
- The item should now be treated as `drop_and_replace`.

### 3. `4hop1__76111_624859_355213_203322`

- Question: `What county shares a border with the county where the singer of Hungry Eyes from the movie Dirty Dancing was born?`
- Gold answer: `Cabarrus County`
- Decision: `drop_and_replace`

Stage 1 judgement:

- `judgement = likely_contaminated`
- `confidence = high`
- `primary_mechanism = dataset_artifact`
- `secondary_mechanisms = ["question_collapse", "unclear"]`

Reasoning:

- The evidence path appears structurally suspect.
- One supporting paragraph identifies Eric Carmen as a `Cleveland, Ohio singer-songwriter`.
- Another supporting paragraph is about `Cleveland, North Carolina`, which is then used to reach `Rowan County` and finally `Cabarrus County`.
- The question wording says `where ... was born`, but the provided evidence does not cleanly establish a birth location through the same entity chain.

Stage 2 decision:

- Do not attempt a minimal rewrite as the primary recovery path.
- This looks like a homonym/entity-linking artifact rather than a clean contamination-only wording issue.

Operator note:

- Replace this question.
- Also flag it upstream as a probable data-quality review item if similar collisions appear elsewhere.

## Recommended Next Action

For this reduced-scope batch, the cleanest operator path is:

1. Mark `2hop__86458_20273` as `drop_and_replace`.
2. Mark `3hop1__222979_40769_64047` as `drop_and_replace`.
3. Mark `4hop1__76111_624859_355213_203322` as `drop_and_replace` and note the likely entity-collision issue.
4. Keep the run-level decision at `stop_and_escalate`.

## Non-Negotiable Reminder

This memo is advisory only.

It does not:

- clear the contamination gate
- authorize an automatic rerun
- upgrade the run to `measurement_validated`
- override the protocol requirement for human approval and lineage tracking
