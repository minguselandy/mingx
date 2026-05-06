# Codex post-development review prompt

Review the current diff against the revised paper boundary and phase guidance.

Read first:

- `AGENTS.md`
- `docs/codex/post-development-review-agent.md`
- `docs/codex/phase-development-guidance.md`
- relevant phase guidance under `docs/codex/phases/`
- relevant docs under `docs/protocols/`
- `docs/paper-alignment-v10.md`

Inputs to consider:

- current git diff
- changed files
- test output supplied by the developer
- generated artifacts, if any

Review focus:

- phase-boundary violations
- claim inflation
- theorem-level wording
- accidental `Vinfo_proxy_certified` emission
- `CandidatePool` treated as core paper artifact
- `gamma_hat` legacy/non-headline alias treated as a submodularity ratio
- `block_ratio_lcb_star` described as degree-adaptive or paper-grade
- diagnostic recomputation introduced during Phase B
- inference of missing materialization order
- inference of excluded candidates
- nondeterministic artifact output
- missing or weakened tests

Use the output format from `docs/codex/post-development-review-agent.md`.

Do not patch before reporting.
