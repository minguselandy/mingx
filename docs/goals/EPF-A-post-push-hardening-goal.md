# Goal: EPF-A post-push hardening

## Terminal State

Allowed terminal states:

* EPF_POST_PUSH_HARDENING_REVIEWABLE
* EPF_POST_PUSH_HARDENING_COMMITTED_LOCAL_ONLY
* EPF_POST_PUSH_HARDENING_BLOCKED

Primary intended state:
EPF_POST_PUSH_HARDENING_REVIEWABLE

## Baseline

* Branch: codex/integrated-validation-workbench
* Starting commit: 426d4b13c20e5bf3a5cedb75f6edb5a12027febd
* Remote branch already pushed and synced
* EPF package already reviewed, committed, and pushed
* Review verdict ACCEPT_WITH_NOTES
* Blocking issues none
* Claim status operational_utility_only / no_claim_upgrade
* Route 5 and Route 8 locked

## Objective

Harden the EPF post-push baseline by addressing review non-blocking notes only:

* API key/base_url hardening
* WS6 nested claim_ledger artifact policy
* claim-boundary preservation

## Non-Objectives

This goal must not perform:

* new large experiments
* paper claim upgrade
* manuscript claim edits
* project claim-ledger edits
* Route 5 unlock
* Route 8 unlock
* measurement_validation claim
* calibrated_proxy_supported claim
* vinfo_proxy_supported claim
* teacher-forced NLL support claim
* metric bridge support claim
* paper evidence claim
* pushing a new hardening commit without explicit approval

## Allowed Files

Likely in-scope files:

* cps/experiments/live_api_evidence_package_factory.py
* tests/experiments/test_live_api_evidence_package_factory.py
* tests/evaluators/*
* docs/experiments/WS6*
* docs/experiments/WS9*
* docs/reviews/WS10*
* docs/paper/WS10*
* configs/workbench/epf_ws6_multibench_operational.yaml, only if needed
* docs/goals/EPF-A-* files

## Forbidden Files and Paths

For the future hardening goal, do not modify or stage:

* .codex/*
* artifacts/operator_inputs/*
* raw API dumps
* raw dataset mirrors
* project claim-ledger edits
* manuscript claim edits outside explicitly listed WS10 positioning-plan docs
* artifacts/experiments/epf_ws6_multibench_operational/workbench_hotpotqa/claim_ledger.json
* artifacts/experiments/epf_ws6_multibench_operational/workbench_project_native/claim_ledger.json
* unrelated Beta/Route4D/Route6C/older WS1 leftovers
* unrelated untracked leftovers

## Hard Constraints

* Do not use git add -A.
* Use explicit selective staging only.
* Do not stage the two WS6 nested claim_ledger.json files.
* Do not weaken paper-boundary guardrails.
* Do not write or commit secrets.
* Do not store raw API responses.
* Do not introduce vLLM, local HF, torch, transformers, or teacher-forced scorer dependencies.
* Do not claim any metric bridge or V-information proxy support.

## Checkpoints

### Checkpoint 1: baseline verification

Run and record:

* git status --short
* git log --oneline -1
* confirm HEAD is 426d4b13c20e5bf3a5cedb75f6edb5a12027febd or a direct descendant if local edits already exist
* confirm remaining untracked files are only known excluded leftovers
* confirm WS6 nested claim_ledger.json files remain untracked and local-only

### Checkpoint 2: API key/base URL hardening

* inspect live API client configuration
* remove generic API_KEY fallback if feasible
* otherwise permit generic API_KEY only with explicit approved DashScope/Qwen-compatible base_url validation
* tests must cover:
  * DASHSCOPE_API_KEY accepted
  * QWEN_API_KEY accepted if currently supported
  * generic API_KEY rejected by default
  * generic API_KEY with non-approved base_url rejected
  * no fallback to local/model-hosted backends

### Checkpoint 3: WS6 nested claim ledger policy

* document generated WS6 nested workbench claim_ledger.json files as shadow-mode local artifacts
* state they are not project claim-ledger edits
* state they must remain excluded from selective commits unless a future explicit ledger-artifact policy approves them
* do not commit existing nested claim_ledger.json files

### Checkpoint 4: claim-boundary verification

* confirm claim status remains operational_utility_only / no_claim_upgrade
* confirm Route 5 and Route 8 remain locked/requested false
* confirm fixed-target teacher-forced NLL remains blocked
* confirm chat logprobs remain operational diagnostics only
* confirm WS5 remains blocked without human/external gold labels

## Required Checks

Run and record:

* git diff --check
* uv run pytest tests/evaluators tests/analysis tests/experiments/test_live_api_evidence_package_factory.py -q
* uv run pytest tests/test_revised_framing_guardrails.py -q
* uv run python -m compileall cps tests
* targeted scan for generic API_KEY fallback behavior
* targeted scan for forbidden active claims:
  * measurement_validation
  * calibrated_proxy_supported
  * vinfo_proxy_supported
  * teacher-forced NLL support
  * metric bridge support
  * paper evidence
* targeted scan confirming Route 5 and Route 8 remain locked
* git status --short after checks

## Commit Policy

* If only documentation/code hardening changes are needed and all checks pass, create one selective local commit.
* Suggested commit message: EPF harden live API client and WS6 artifact policy
* Use explicit path staging only.
* Do not stage unrelated leftovers.
* Do not stage WS6 nested claim_ledger.json files.
* Do not push the new hardening commit unless explicitly approved after final report.

## Blocker Policy

If blocked:

* stop with terminal state EPF_POST_PUSH_HARDENING_BLOCKED
* produce a blocker report with:
  * blocker reason
  * files inspected
  * why no safe change was made
  * claim-boundary status
  * recommended next action

## Final Report Format

Return:

* terminal state
* current branch
* starting commit
* new commit hash, if any
* files changed
* files explicitly excluded
* tests/checks run and results
* API key/base_url hardening result
* WS6 nested claim_ledger artifact policy result
* confirmation that WS6 nested claim_ledger.json files remain uncommitted/unpushed
* confirmation that claim status remains operational_utility_only/no_claim_upgrade
* confirmation that Route 5 and Route 8 remain locked
* confirmation that no push was performed unless explicitly approved
