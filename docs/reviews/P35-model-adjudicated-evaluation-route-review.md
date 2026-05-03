# P35 Model-Adjudicated Empirical Evaluation Route Review

```yaml
phase_id: P35
phase_title: Model-Adjudicated Empirical Evaluation Route Revision
document_type: protocol_revision_review
branch: codex/p35-model-adjudicated-evaluation-route
p35_scope: documentation/protocol_revision_only
runtime_code_changed: false
tests_added: false
source_manuscript_changed: false
live_api_run: false
human_labels_fabricated: false
kappa_fabricated: false
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
original_repo_synced: false
```

## 1. Phase Summary

P35 revises the empirical validation protocol and operator runbooks to support
two explicit empirical routes after EV2 controlled live pilot evidence:

- Route A: human-labeled measurement validation route.
- Route B: fully automated model-adjudicated evaluation route.

The revision acknowledges that the project may proceed without human annotation
by using DeepSeek V4 Flash prelabels, Codex subagent audit, and Codex model
adjudication. The claim boundary remains strict: Route B cannot produce
`measurement_validated`.

## 2. Changed Files

- `docs/protocols/empirical-validation-protocol.md`
- `docs/experiments/empirical-evidence-package.md`
- `docs/runbooks/live-pilot-operator-runbook.md`
- `docs/runbooks/live-pilot-execution-decision.md`
- `docs/reviews/P35-model-adjudicated-evaluation-route-review.md`

No runtime modules, tests, source manuscript files, generated evidence outputs,
or reference files were changed.

## 3. Reason For Adding Route B

Route A remains the only path that can approach measurement validation because it
requires real human labels, human-human kappa, contamination closure, fresh
metric bridge evidence, and conservative claim gate allow.

Route B provides a faster, cheaper, fully automated evaluation path for pilot and
operational evidence. It can help triage cases, compare model-conditioned
behavior, and reduce annotation workload, but it has lower claim strength because
it has no human labels and no human-human kappa.

## 4. EV3-Lite Definition

`EV3-lite model-adjudicated evaluation` is defined as a fully automated route
that uses:

- DeepSeek V4 Flash prelabels;
- Codex subagent audit;
- Codex model adjudication;
- `model_adjudicated_labels.jsonl`;
- contamination audit status;
- metric bridge status;
- conservative claim gate review.

EV3-lite does not require human labels or human-human kappa. It cannot support
`measurement_validated`, `human_labeled_validation`, human-human kappa claims,
scientific validation, or deployed V-information certification.

## 5. Route A / Route B Comparison

| Route | Requires human labels | Requires human-human kappa | Uses V4 Flash prelabels | Uses Codex subagent audit | Uses Codex model adjudication | Can claim measurement_validated | Allowed maximum claim | Main risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Route A: Human-labeled measurement validation | Yes | Yes | Optional aid only | Optional aid only | No | Only if all EV3/EV4 gates and claim gate allow | `measurement_validated_candidate` before final gate closure | Cost, schedule, annotator reliability, contamination, bridge closure. |
| Route B: Fully automated model-adjudicated evaluation | No | No | Yes | Yes | Yes | No | `model_adjudicated_pilot_only` or `operational_utility_only` | Automated judge evidence may be overtrusted as human validation. |

## 6. Claim Ladder Changes

P35 adds these Route B claim levels to the empirical protocol:

- `model_adjudicated_pilot_only`
- `automated_judge_evidence`
- `annotation_workload_reduction_evidence`
- `operational_utility_only`

These claim levels are evidence-boundary labels, not validation upgrades. They
do not replace the existing conservative claim gate.

## 7. Allowed Claims For Route B

Route B may support:

- `model_adjudicated_pilot_only`;
- `automated_judge_evidence`;
- `annotation_workload_reduction_evidence`;
- `operational_utility_only`.

These claims must be scoped to the automated model-adjudicated route and the
fixed run artifacts.

## 8. Denied Claims For Route B

Route B denies:

- `measurement_validated`;
- `human_labeled_validation`;
- `human_human_kappa_established`;
- `scientific_validation_completed`;
- deployed V-information certification.

Model-adjudicated labels are not human labels. Codex adjudication is not human
review. LLM/Codex agreement is not human-human kappa.

## 9. Risk Register

| Risk | Mitigation |
| --- | --- |
| Model adjudication may be overtrusted. | Keep Route B claim ceiling at `model_adjudicated_pilot_only` or `operational_utility_only`. |
| Codex audit may be mistaken for human review. | State that Codex audit is automated audit evidence, not human review. |
| Model-adjudicated labels may be mistaken for human labels. | Use `model_adjudicated_labels.jsonl` only; never `human_labels.jsonl`. |
| Automatic judge bias. | Treat outputs as pilot or operational evidence only. |
| Self-consistency does not imply correctness. | Deny scientific validation and require claim gate review. |
| No human-human kappa. | Deny `human_human_kappa_established` and `measurement_validated`. |
| Cannot support `measurement_validated`. | Preserve the Route A gate for validation-level claims. |
| May still be useful as pilot evidence or operational evidence. | Report only automated judge, workload reduction, or operational evidence claims. |

## 10. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
pytest tests/test_model_adjudicated_labels.py -q
pytest tests/test_empirical_evidence_package.py -q
pytest tests/test_llm_assisted_prelabels.py -q
pytest tests/test_prelabel_subagent_audit.py -q
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |
| `pytest tests/test_model_adjudicated_labels.py -q` | 10 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |
| `pytest tests/test_llm_assisted_prelabels.py -q` | 16 passed |
| `pytest tests/test_prelabel_subagent_audit.py -q` | 12 passed |

## 11. Known Limitations

- P35 does not implement new runtime integration for Route B.
- P35 does not modify the empirical evidence package code.
- P35 does not run live APIs.
- P35 does not create human labels.
- P35 does not compute kappa.
- P35 does not close contamination or metric bridge gates.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.

## 12. Next Recommended Phase

Recommended next phase:

```text
P36 Model-Adjudicated Evidence Package Integration
```

This is preferred unless the operator provides live V4 Flash credentials and an
approved output root for live prelabel generation.

## 13. Claim Boundary Restatement

- P35 is documentation/protocol revision only.
- Route B does not require human labels.
- Route B does not compute human-human kappa.
- Route B cannot claim `measurement_validated`.
- No live API was run.
- No human labels were fabricated.
- No kappa was fabricated.
- No source manuscript edit was made.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
