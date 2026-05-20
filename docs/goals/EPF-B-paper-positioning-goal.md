# Goal: EPF-B paper-positioning integration

## Terminal State

Allowed terminal states:

* EPF_PAPER_POSITIONING_PATCH_REVIEWABLE
* EPF_PAPER_POSITIONING_PATCH_COMMITTED_LOCAL_ONLY
* EPF_PAPER_POSITIONING_BLOCKED

Primary intended state:
EPF_PAPER_POSITIONING_PATCH_REVIEWABLE

## Baseline

* Branch: codex/integrated-validation-workbench
* Starting commit: 0f430e61eb3e8fe92cf3a0a0dd7079f13d43364a
* Remote branch already pushed and synced
* EPF baseline package already reviewed, committed, and pushed
* EPF-A hardening already committed and pushed
* Current claim status: operational_utility_only / no_claim_upgrade
* Route 5 and Route 8 locked
* True fixed-target teacher-forced NLL blocked
* WS5 measurement validation blocked without human/external gold labels
* WS6 nested claim_ledger.json artifacts remain local-only exclusions

## Objective

Integrate the live-API-only EPF result into paper-facing documentation as a backend-constrained, reviewable candidate evidence package factory, while preserving all claim boundaries.

The future execution should:

* use WS10 paper-positioning patch plan as the source plan
* update paper/evidence documentation only where explicitly allowed
* clarify that EPF provides operational diagnostics and candidate evidence packages under live-API constraints
* explicitly state that EPF does not establish teacher-forced NLL support, metric bridge support, calibrated proxy support, V-information proxy support, measurement validation, paper evidence, or global selector superiority
* preserve operational_utility_only / no_claim_upgrade

## Non-Objectives

This goal must not perform:

* new experiments
* new API calls
* code changes
* test changes unless only a documentation guardrail requires it
* paper claim upgrade
* project claim-ledger upgrade
* Route 5 unlock
* Route 8 unlock
* measurement_validation claim
* calibrated_proxy_supported claim
* vinfo_proxy_supported claim
* teacher-forced NLL support claim
* metric bridge support claim
* paper evidence claim
* selector superiority beyond already scoped operational comparisons
* committing or pushing without explicit approval

## Allowed Files

For the future paper-positioning execution, likely allowed files:

* docs/archive/context_projection_fixed_v12.md
* docs/paper-alignment-v12.md
* docs/paper/v12-evidence-ledger.md
* docs/paper/v12-manuscript-integration-checklist.md
* docs/paper/WS10-paper-positioning-patch-plan.md, read or update only if needed
* docs/reviews/WS10-candidate-evidence-independent-review-template.md, read only unless a review-template consistency note is needed
* docs/experiments/WS0-WS10*, read only unless cross-reference wording is required
* docs/goals/EPF-B-* files

## Forbidden Files and Paths

For the future goal, do not modify or stage:

* cps/*
* tests/*
* configs/*
* artifacts/operator_inputs/*
* raw API dumps
* raw dataset mirrors
* .codex/*
* project claim-ledger edits outside explicitly allowed paper evidence ledger docs
* generated nested WS6 claim_ledger.json artifacts:
  * artifacts/experiments/epf_ws6_multibench_operational/workbench_hotpotqa/claim_ledger.json
  * artifacts/experiments/epf_ws6_multibench_operational/workbench_project_native/claim_ledger.json
* unrelated Beta/Route4D/Route6C/older WS1 leftovers
* teacher-forced backend leftovers
* unrelated untracked leftovers

## Hard Constraints

* Do not use git add -A.
* Use explicit selective staging only.
* Do not stage WS6 nested claim_ledger.json files.
* Do not modify code unless the future goal is explicitly revised and reviewed.
* Do not run live API calls.
* Do not generate new experimental artifacts.
* Do not weaken paper-boundary guardrails.
* Do not write or commit secrets.
* Do not introduce timestamps, UUIDs, absolute paths, or machine-specific values into deterministic goal state files.
* Do not claim any metric bridge, calibrated proxy, V-information proxy, measurement validation, teacher-forced NLL support, or paper evidence.
* Keep Route 5 and Route 8 locked.

## Required Paper Positioning Content

The future execution must add or refine wording equivalent to:

"Under the available live-API backend, the EPF does not expose true fixed-target teacher-forced continuation scoring. Therefore, EPF outputs are reported as backend-constrained, reviewable candidate operational evidence packages. Chat-logprob confidence, constrained label-generation proxies, weak-source judge audits, multi-benchmark operational robustness summaries, and uncertainty-bounded reports are operational diagnostics or candidate evidence only. They do not establish metric bridge support, calibrated proxy support, V-information proxy support, measurement validation, paper evidence, or global selector superiority."

The future execution should include a compact status table where appropriate:

| Evidence component | Status | Claim ceiling |
| --- | --- | --- |
| WS1 teacher-forced NLL closure | blocked | no metric bridge |
| WS2 chat-logprob confidence | available | operational diagnostic only |
| WS3 constrained label proxy | available | candidate proxy only |
| WS4 judge weak-source audit | available | weak supervision only |
| WS5 hybrid validation | blocked | no measurement validation |
| WS6 multi-benchmark operational robustness | available | scoped operational candidate |
| WS8 uncertainty-bounded reporting | available | candidate operational reporting |

## Checkpoints

### Checkpoint 1: baseline verification

Run and record:

* git status --short
* git log --oneline -1
* confirm HEAD is 0f430e61eb3e8fe92cf3a0a0dd7079f13d43364a or a direct descendant if local edits already exist
* confirm remote branch is synced unless local goal-doc setup edits exist
* confirm known untracked files are excluded leftovers only
* confirm WS6 nested claim_ledger.json files remain local-only and untracked

### Checkpoint 2: source inspection

* read docs/paper/WS10-paper-positioning-patch-plan.md
* read EPF candidate package final status and claim request artifacts if needed
* read current paper/evidence docs before editing
* identify exact sections to patch
* do not edit yet if the intended patch would require claim upgrade

### Checkpoint 3: safe paper positioning patch

* update only allowed paper/evidence documentation
* add EPF as a candidate operational evidence factory, not paper-grade evidence
* preserve formal V-information framing as a theoretical anchor, not empirically validated by EPF
* explicitly state backend limitation and blocked teacher-forced NLL path
* explicitly state WS5 is blocked without human/external gold
* keep denied claims explicit

### Checkpoint 4: claim-boundary verification

* confirm operational_utility_only / no_claim_upgrade remains
* confirm no active measurement_validation claim
* confirm no active calibrated_proxy_supported claim
* confirm no active vinfo_proxy_supported claim
* confirm no active teacher-forced NLL support claim
* confirm no active metric bridge support claim
* confirm no active paper evidence claim
* confirm Route 5 and Route 8 remain locked
* confirm WS6 nested claim_ledger.json artifacts remain uncommitted/unpushed

## Required Checks

Run and record:

* git diff --check
* uv run pytest tests/test_revised_framing_guardrails.py -q
* optional documentation-only grep/scan for forbidden active claims:
  * measurement_validation
  * calibrated_proxy_supported
  * vinfo_proxy_supported
  * teacher-forced NLL support
  * metric bridge support
  * paper evidence
  * selector superiority
* targeted scan confirming Route 5 and Route 8 remain locked/requested false where referenced
* targeted scan confirming EPF remains operational_utility_only/no_claim_upgrade
* git status --short after checks

If code/tests are not touched, do not run the full EPF test suite unless the future executor believes it is necessary.

## Commit Policy

* Primary intended terminal state is REVIEWABLE, not committed.
* If all checks pass and the user explicitly approves, create one selective local commit.
* Suggested commit message:
  EPF integrate live-API evidence factory paper positioning
* Use explicit path staging only.
* Do not stage unrelated leftovers.
* Do not stage WS6 nested claim_ledger.json files.
* Do not push the new paper-positioning commit unless explicitly approved after final report.

## Blocker Policy

If blocked:

* stop with terminal state EPF_PAPER_POSITIONING_BLOCKED
* produce a blocker report with:
  * blocker reason
  * files inspected
  * why no safe paper wording was applied
  * claim-boundary status
  * recommended next action

Block if:

* safe wording cannot be added without implying paper evidence
* current docs already contain conflicting upgraded claims that require broader repair
* updating paper docs would require code or artifact changes
* Route 5 or Route 8 would need to be unlocked
* WS5 measurement validation would need human/external gold labels
* forbidden files would need to be staged

## Final Report Format

Return:

* terminal state
* current branch
* starting commit
* files inspected
* files changed
* files explicitly excluded
* wording summary
* checks run and results
* claim-boundary confirmation
* confirmation that claim status remains operational_utility_only/no_claim_upgrade
* confirmation that true fixed-target teacher-forced NLL remains blocked
* confirmation that WS5 measurement validation remains blocked
* confirmation that Route 5 and Route 8 remain locked
* confirmation that WS6 nested claim_ledger.json files remain uncommitted/unpushed
* commit hash, if any
* push status
