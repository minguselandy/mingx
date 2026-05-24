# Mingx POST-LAPI Global Constraints

Current reported repository state:
- branch: codex/integrated-validation-workbench
- HEAD: f38d3aa
- origin/codex/integrated-validation-workbench: f38d3aa
- index: empty
- PR is reported as merged, but local checkout may still be the feature branch
- historical untracked leftovers exist and must remain isolated

Completed mainline:
- EPF baseline / EPF-A / EPF-B / EPF-FINAL
- PAPER-RS docs restructuring
- LAPI-1 through LAPI-8

Current empirical claim:
- operational_utility_only/no_claim_upgrade

Hard project locks:
- Route 5 remains locked
- Route 8 remains locked
- true fixed-target teacher-forced NLL remains unsupported
- fixed-target continuation scoring remains unsupported
- WS5 human/external measurement validation remains blocked
- raw API responses must not be stored

Denied claims:
- measurement validation
- human/external gold validation
- teacher-forced NLL support
- fixed-target continuation scoring support
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- paper-grade evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

Allowed claim classes:
- operational replay evidence
- candidate operational evidence
- model-adjudicated weak evidence
- sufficiency / abstention diagnostic
- replayable artifact evidence
- fail-closed bridge audit
- scoped operational improvement under matched budgets

Global implementation constraints:
- Do not use vLLM.
- Do not use local HF / torch / transformers scorer.
- Do not use APIs other than the DashScope-compatible live API when a run goal explicitly permits live API.
- Configuration goals must not run live API calls.
- Do not use git add -A.
- Do not stage untracked leftovers.
- Do not delete or clean historical leftovers unless explicitly instructed by the project owner.
- Do not store raw API responses.
- Preserve compact provenance, hashes, normalized enums, prompt hashes, model snapshot, endpoint, and raw_response_stored=false fields where applicable.
