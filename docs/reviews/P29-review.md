# P29 Live Pilot Operator Runbook Review

```yaml
phase_id: P29
phase_title: Live Pilot Operator Runbook
document_type: runbook_review
branch: codex/p29-live-pilot-operator-runbook
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
labels_fabricated: false
kappa_fabricated: false
contamination_pass_fabricated: false
runtime_code_changed: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P29 adds an operator-facing runbook for a future controlled EV2/EV3 empirical
pilot using the P25-P28 validation infrastructure. It documents pilot design,
DeepSeek V4 Flash / Pro model-condition policy, live gates, human labeling,
kappa thresholds, contamination audit, metric bridge freshness, claim gate
mapping, budget controls, and manuscript impact.

P29 is runbook only. It does not run live APIs, add API clients, import external
SDKs, fabricate labels, fabricate kappa, fabricate contamination pass, unblock
P04/P09, or claim `measurement_validated`.

## 2. Changed Files

- `docs/runbooks/live-pilot-operator-runbook.md`
- `docs/reviews/P29-review.md`

## 3. Runbook Stages Documented

The runbook documents:

- Stage 0: Dry-run rehearsal
- Stage 1: Controlled live pilot, EV2
- Stage 2: Human labeling, EV3
- Stage 3: Kappa report generation
- Stage 4: Contamination audit
- Stage 5: Metric bridge freshness review
- Stage 6: Empirical evidence package build
- Stage 7: Claim gate decision
- Stage 8: Manuscript patch decision

Stage 0 is dry-run only. Stage 1 requires explicit operator approval and live
gates. Stage 8 defers manuscript empirical-result wording until claim gate
review.

## 4. DeepSeek V4 Flash / Pro Model Policy

The runbook defines two model conditions:

| Model alias | Role | First-run size | Expanded size | Purpose |
| --- | --- | --- | --- | --- |
| `deepseek_v4_flash` | `primary_pilot_model` | 30-50 cases | 100-200 cases | Cost-efficient primary pilot condition. |
| `deepseek_v4_pro` | `strong_model_audit_subset` | 10-20 matched cases | 50-100 matched cases if budget allows | Stronger-model audit subset. |

DeepSeek V4 Flash and DeepSeek V4 Pro are model conditions, not validation
authorities. Actual provider endpoints and model names are operator-filled
manifest fields and are not hard-coded in source code.

## 5. Live Gates Documented

The runbook requires:

- clean git state;
- exact commit and branch recorded;
- fixed model endpoint/name/alias;
- frozen prompt template;
- fixed cases and conditions;
- empty or archived output root;
- `CPS_ALLOW_LIVE_API=1` only during execution;
- `operator_approval: true`;
- budget cap;
- credentials configured outside the repo;
- no unit-test live calls;
- labeler, contamination reviewer, and metric bridge reviewer identified.

Missing prerequisites fail closed.

## 6. Claim Gate Mapping Documented

The runbook maps evidence states to conservative claim levels, including:

- dry-run only => `engineering_smoke_only`;
- live run without labels => `controlled_live_pilot_only`;
- missing kappa => not `measurement_validated`;
- low kappa => `pilot_only` or weak evidence;
- contamination failure => `pilot_only`;
- stale bridge => `operational_utility_only` or `ambiguous`;
- Flash/Pro favorable live outputs without labels/kappa => not
  `measurement_validated`;
- complete favorable evidence => `measurement_validated_candidate`;
- `measurement_validated` only if the existing claim gate explicitly allows it.

## 7. Cost-Control Section Documented

The runbook documents:

- Flash as the primary cost-efficient pilot model;
- Pro as a stronger-model audit subset;
- predeclared budget cap;
- stopping when projected cost exceeds cap;
- token, case, and condition count recording;
- no silent sample-size expansion;
- bounded and recorded retries;
- no exact prices unless supplied by the operator later.

## 8. Denied Claims

- `measurement_validated` is not claimed.
- Empirical validation is not completed.
- Live API success alone is not measurement validation.
- DeepSeek V4 Flash does not validate the method.
- DeepSeek V4 Pro does not validate the method.
- High kappa alone is not measurement validation.
- Contamination pass alone is not measurement validation.
- Synthetic/proxy evidence does not certify deployed V-information
  submodularity.
- Proxy-regime certification is not deployed V-information certification.
- Replay package completeness is not scientific validation.

## 9. Known Limitations

- P29 does not add CLI wrappers.
- P29 does not run dry-run rehearsal.
- P29 does not run live APIs.
- P29 does not collect labels.
- P29 does not compute kappa for a real pilot.
- P29 does not perform contamination audit.
- P29 does not close metric bridge freshness.
- P29 does not update the manuscript.
- P04 and P09 remain operator-required.

## 10. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
pytest tests/test_controlled_live_pilot.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_contamination_audit.py -q
pytest tests/test_empirical_evidence_package.py -q
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_contamination_audit.py -q` | 9 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |

## 11. Next Recommended Phase

Next recommended phase:

```text
P30 Operator-Approved Dry-Run Rehearsal
```

P30 should execute only a dry-run rehearsal unless operators separately approve a
live run. It should not claim `measurement_validated`.

## 12. Claim Boundary

- P29 is runbook only.
- No live API was run.
- DeepSeek V4 Flash / Pro are model conditions, not validation authorities.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
