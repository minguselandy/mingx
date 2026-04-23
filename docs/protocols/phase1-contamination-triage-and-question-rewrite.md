# Phase 1 Contamination Triage and Question Rewrite

**Purpose:** define the operator workflow for using AI as an assistant after a Phase 1 contamination gate failure.

**Status:** active execution protocol for human-in-the-loop triage. This document does not override the scientific gate in `phase1-protocol.md`.

---

## 1. What This Workflow Is For

Use this workflow when `exports/contamination_diagnostics.json` reports `gate_decision = fail`, or when specific questions have `baseline_logp > log(0.5)`.

The goal is not to auto-clear the gate. The goal is to help the operator answer two narrower questions:

1. Is the failure likely caused by question wording that makes the answer recoverable from the question alone?
2. If yes, is there a minimal rewrite that preserves the same gold answer and hop structure while reducing question-only answerability?

If the likely cause is broad pretraining familiarity, a memorized public fact, or a chain that collapses even after wording cleanup, the correct action is usually **drop and replace**, not endless rewriting.

---

## 2. Non-Negotiable Rules

- AI review is advisory only. It does not change `gate_decision`.
- Do not auto-rerun the protocol from rewritten questions without explicit human approval and recorded lineage.
- Rewrites must preserve the same gold answer.
- Rewrites must preserve the same intended hop structure.
- Rewrites must not inject facts unsupported by the MuSiQue evidence.
- If contamination still appears likely after a minimal rewrite, reject the item and replace it with another sampled question.

---

## 3. Two-Stage AI Review

### 3.1 Stage 1: Question-only contamination judgement

Ask AI to inspect the question **without** the gold answer first.

The Stage 1 output should classify the likely failure mechanism into one of these buckets:

- `direct_leakage`
- `near_unique_entity_chain`
- `memorized_public_fact`
- `question_collapse`
- `dataset_artifact`
- `unclear`

This stage answers: "Could a strong frontier LM likely recover the answer from prior knowledge, even without context paragraphs?"

### 3.2 Stage 2: Rewrite planning with evidence

Only after Stage 1 should AI inspect:

- the gold answer
- supporting paragraph titles and excerpts

The Stage 2 task is to propose the **smallest** rewrite that reduces question-only answerability while keeping the answer and evidence path intact.

Valid outcomes:

- `rewrite_recommended`
- `drop_and_replace`
- `needs_human_only`

---

## 4. Rewrite Acceptance Criteria

Accept an AI-proposed rewrite only if all of the following hold:

- the gold answer is unchanged
- the rewrite remains answerable from the supporting evidence
- the rewrite does not collapse the multi-hop chain into a one-hop lookup
- the rewrite removes or weakens the leakage mechanism identified in Stage 1
- a human reviewer agrees that the revised wording is still natural and task-valid

Reject the rewrite if any of the following happens:

- the rewrite introduces unsupported facts
- the rewrite becomes vague or unnatural just to hide the answer
- the question still strongly points to a near-unique answer from prior knowledge alone
- the rewrite changes the reasoning target or answer identity

---

## 5. Default Decision Policy

When contamination fails, keep the repository default:

- `stop_and_escalate`
- `auto_restrict_to_uncontaminated_subset = false`
- `auto_rerun_protocol_full = false`
- `auto_upgrade_to_measurement_validated = false`

This review workflow exists to prepare a better operator decision, not to bypass that decision.

---

## 6. Review Packet Export

Use the repository script below to export a manual review packet:

```bash
python scripts/export_contamination_review_packet.py \
  --run-summary artifacts/phase1/live_mini_batch/exports/run_summary.json \
  --json-out artifacts/phase1/live_mini_batch/exports/contamination_review_packet.json \
  --markdown-out artifacts/phase1/live_mini_batch/exports/contamination_review_packet.md
```

The script resolves:

- `contamination_diagnostics.json`
- `calibration_manifest.json`
- the original `sample_manifest_v1.json`

It then emits a packet containing only the above-threshold questions, along with:

- question text
- gold answer
- supporting paragraph excerpts
- heuristic signals
- a Stage 1 question-only prompt
- a Stage 2 rewrite-planning prompt

---

## 7. Suggested Operator Sequence

1. Run the export script after a contamination fail.
2. Use the Stage 1 prompt first and record AI's contamination judgement.
3. Use the Stage 2 prompt only for questions where rewrite still looks plausible.
4. Review the rewrite manually against the acceptance criteria above.
5. Either:
   - approve a minimal rewrite and record lineage, or
   - drop and replace the question, or
   - escalate to Phase 0 / protocol revision if the failure mode is structural.

---

## 8. Current Scope Note

This workflow is especially relevant for the reduced-scope `live-mini-batch` run, where the current contamination outcome is a scientific stop rather than an engineering failure.

Do not describe a run as `measurement_validated` just because AI produced a plausible rewrite. The gate remains failed until a human-approved follow-up run is executed and evaluated under the same protocol semantics.
