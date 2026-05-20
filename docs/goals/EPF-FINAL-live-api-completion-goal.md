# Goal: EPF-FINAL live-API-only completion

## Baseline

* Branch: codex/integrated-validation-workbench
* Starting HEAD: ba67696554ebebcbb9fcb615dfaa05a610f9513d
* EPF baseline, EPF-A hardening, and EPF-B paper positioning have been committed and pushed.
* Current claim status: operational_utility_only/no_claim_upgrade
* True fixed-target teacher-forced NLL remains blocked.
* WS5 human/external measurement validation remains blocked.
* Route 5 and Route 8 remain locked.
* Known excluded leftovers remain local-only and must not be staged.

## Objective

Complete the remaining live-API-only EPF work as one bounded long-horizon task. The goal is to finish a reviewable EPF candidate evidence system using LLM-generated silver labels and operational diagnostics, not to upgrade claims.

The final system should produce a reviewable candidate evidence package that clearly separates:

* LLM-generated silver labels from human/external gold labels
* operational diagnostics from measurement validation
* candidate evidence from accepted paper evidence
* live-API-only scoring from true fixed-target teacher-forced NLL

## Terminal States

Allowed terminal states:

* EPF_FINAL_REVIEWABLE
* EPF_FINAL_COMMITTED_LOCAL_ONLY
* EPF_FINAL_BLOCKED

Primary intended state:
EPF_FINAL_REVIEWABLE

## Milestone 1: Baseline Verification

Required actions:

* Verify branch and HEAD.
* Inspect current EPF artifacts, claim_request, final_status, paper positioning docs, and EPF-B state.
* Confirm excluded leftovers remain local-only.
* Confirm Route 5 and Route 8 remain locked.

Required checks:

* `git branch --show-current`
* `git rev-parse HEAD`
* `git status --short`
* confirm HEAD is ba67696554ebebcbb9fcb615dfaa05a610f9513d or a direct descendant
* confirm no excluded leftovers are staged

## Milestone 2: LLM-Generated Silver-Label Factory

Implement or extend live-API-only silver-label generation using approved DashScope/Qwen-compatible API configuration only.

Required behavior:

* Use strong LLM label generation as model-adjudicated silver labels, not human/external gold labels.
* Ensure the evaluated selector/policy is not used to generate its own labels.
* Store normalized enum labels, confidence, provenance, prompt hash, input hash, model id, and evidence hash.
* Do not store raw API responses.
* Do not store long free-form rationales unless hashed or summarized into safe normalized fields.
* Add uncertainty/disagreement buckets rather than forcing ambiguous labels.
* Mark all outputs as LLM-generated silver labels / model-adjudicated candidate evidence.

Required safeguards:

* Silver-label generation must not imply human measurement validation.
* Silver-label generation must not imply external gold labels.
* Silver-label generation must not unlock Route 5 or Route 8.
* Silver-label generation must not create project claim-ledger edits.

## Milestone 3: Silver-Label Operational Evaluation

Use silver labels only for operational candidate evaluation.

Required outputs:

* label generation report
* uncertainty/disagreement report
* scoped operational evaluation summary

Required wording:

* Do not call the results measurement_validation.
* Do not call the labels human gold, external gold, or paper-grade labels.
* Report results as candidate operational evidence under live-API-only constraints.
* Preserve the distinction between operational diagnostic evidence and accepted paper evidence.

## Milestone 4: Final EPF Candidate Package Refresh

Refresh or create final EPF package artifacts under a clearly named EPF final directory.

Required artifact directories:

* artifacts/experiments/epf_final/*
* artifacts/experiments/epf_c_silver_labels/*

Required artifacts should include:

* label_schema.json
* silver_label_manifest.json
* label_generation_report.json
* uncertainty_disagreement_report.json
* final_epf_manifest.json
* final_claim_request.json
* independent_review_checklist.md

Every generated artifact must include or reference:

* evidence_class
* claim_ceiling
* denied_claims
* provenance
* review_status

Required artifact policy:

* Store normalized outputs and compact reports only.
* Do not store raw API responses.
* Do not store secrets.
* Do not create raw dataset mirrors.
* Keep artifacts under the repository's storage policy.

## Milestone 5: Documentation Sync

Update EPF docs and paper/evidence docs only as needed.

Required framing:

* Frame EPF as a backend-constrained, reviewable candidate operational evidence package factory.
* Explicitly state that LLM-generated labels are silver/model-adjudicated labels, not human/external gold.
* Preserve formal V-information as theoretical anchor only.

Explicitly preserve:

* no teacher-forced NLL support
* no metric bridge support
* no calibrated proxy support
* no V-information proxy support
* no measurement validation
* no paper evidence
* no global selector superiority

## Allowed Files

The future goal may modify only files in these scopes when needed:

* cps/evaluators/live_api_*
* cps/analysis/*
* cps/experiments/live_api_evidence_package_factory.py
* cps/experiments/workbench/*
* tests/evaluators/*
* tests/analysis/*
* tests/experiments/*
* configs/workbench/*
* docs/experiments/EPF*
* docs/paper/WS10-paper-positioning-patch-plan.md
* docs/paper-alignment-v12.md
* docs/paper/v12-evidence-ledger.md
* docs/paper/v12-manuscript-integration-checklist.md
* docs/goals/EPF-FINAL-live-api-completion-goal.md
* artifacts/experiments/epf_final/*
* artifacts/experiments/epf_c_silver_labels/*

## Forbidden Files and Paths

Do not modify or stage:

* .codex/*
* artifacts/operator_inputs/*
* raw API dumps
* raw dataset mirrors
* project claim-ledger edits unless explicitly listed
* manuscript claim upgrade edits
* WS6 nested claim_ledger.json artifacts
* unrelated Beta/Route4D/Route6C/WS0/WS1 leftovers
* teacher-forced backend leftovers
* unrelated untracked leftovers

Known WS6 nested claim_ledger.json artifacts that must remain uncommitted:

* artifacts/experiments/epf_ws6_multibench_operational/workbench_hotpotqa/claim_ledger.json
* artifacts/experiments/epf_ws6_multibench_operational/workbench_project_native/claim_ledger.json

## Claim Constraints

Do not claim:

* measurement_validation
* human/external gold validation
* teacher-forced NLL support
* metric bridge support
* calibrated_proxy_supported
* vinfo_proxy_supported
* paper evidence
* global selector superiority
* Route 5 unlock
* Route 8 unlock

Required claim posture:

* Current claim status remains operational_utility_only/no_claim_upgrade.
* Silver labels are LLM-generated/model-adjudicated candidate evidence only.
* EPF final outputs are reviewable candidate evidence packages, not accepted evidence.
* Independent review is required before any later candidate claim can be upgraded.
* Route 5 and Route 8 remain locked.
* True fixed-target teacher-forced NLL remains blocked.
* WS5 human/external measurement validation remains blocked.

## Required Checks

Run and record:

* `git diff --check`
* `uv run pytest tests/evaluators tests/analysis tests/experiments/test_live_api_evidence_package_factory.py -q`
* `uv run pytest tests/test_revised_framing_guardrails.py -q`
* `uv run python -m compileall cps tests`
* JSON/JSONL validation for generated EPF final artifacts
* targeted scan confirming no raw API responses are stored
* targeted scan confirming no active measurement_validation or gold-label claim
* targeted scan confirming no active calibrated_proxy_supported or vinfo_proxy_supported claim
* targeted scan confirming no teacher-forced NLL support claim
* targeted scan confirming Route 5 and Route 8 remain locked
* secret scan over intended files/artifacts
* forbidden-path scan over staged/changed files

Required final repository checks:

* `git status --short`
* staged-file list if a commit is prepared
* changed-file size scan
* confirmation that forbidden leftovers remain uncommitted

## Commit Policy

* Primary intended state is EPF_FINAL_REVIEWABLE.
* If all checks pass and the package is self-contained, a single selective local commit is allowed.
* Do not push without explicit user approval.
* Use explicit staging only.
* Do not use git add -A.
* Do not stage unrelated leftovers.
* Do not stage WS6 nested claim_ledger.json artifacts.
* Do not stage raw API dumps, raw dataset mirrors, operator_inputs, .codex files, or project claim-ledger upgrades.

Suggested commit message:

`EPF complete live-API silver-label candidate evidence package`

## Blocker Policy

Stop with terminal state EPF_FINAL_BLOCKED if:

* approved DashScope/Qwen-compatible live API configuration is unavailable
* safe LLM-generated silver labels cannot be produced without raw API responses
* selector/policy self-labeling cannot be prevented
* generated labels cannot be normalized and schema-validated
* uncertainty/disagreement cannot be represented without forcing ambiguous labels
* EPF final artifacts would exceed storage policy
* paper/evidence docs cannot be updated without implying claim upgrade
* any required check fails and cannot be repaired within the allowed file scope
* Route 5 or Route 8 would need to be unlocked
* WS5 measurement validation would require unavailable human/external gold labels
* true fixed-target teacher-forced NLL support would need to be claimed
* forbidden leftovers would need to be staged
* secrets, raw API responses, raw dataset mirrors, or operator_inputs would be introduced

When blocked, write a precise blocker report explaining:

* blocker reason
* files inspected
* partial outputs, if any
* claim-boundary status
* recommended next action

## Final Report Format

Return:

* terminal state
* current branch
* starting HEAD
* files changed
* artifacts generated
* API usage summary if live calls were made
* label schema summary
* uncertainty/disagreement handling
* checks run and results
* claim-boundary confirmation
* confirmation that claim status remains operational_utility_only/no_claim_upgrade
* confirmation that true fixed-target teacher-forced NLL remains blocked
* confirmation that WS5 human/external measurement validation remains blocked
* confirmation that Route 5 and Route 8 remain locked
* confirmation that forbidden leftovers remain uncommitted
* commit hash if committed
* push status

## Future Codex CLI Command

Use this command later; do not run it during goal setup:

`/goal Execute docs/goals/EPF-FINAL-live-api-completion-goal.md until one of its declared terminal states is reached. Complete the live-API-only EPF silver-label candidate evidence package without upgrading claims, follow its allowed and forbidden paths exactly, run the required checks, use selective staging only if committing, and stop with EPF_FINAL_BLOCKED rather than weakening claim boundaries.`
