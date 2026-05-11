# Review Agent Design for mingx

## Purpose

The review agent audits Codex-generated changes after implementation. It is separate from the development agent.

The review agent's primary responsibility is to prevent:

- phase drift
- claim inflation
- paper-boundary regression
- nondeterministic replay artifacts
- insufficient tests
- silent reconstruction of missing evidence

## Agent type

Recommended implementation options:

1. **PR review agent**
   Run through Codex GitHub review or GitHub Action on pull requests.

2. **Local review agent**
   Run with Codex CLI `/review` or `codex exec` against a working tree before committing.

3. **Subagent in a larger Codex workflow**
   Use when multiple independent checks are useful, but keep the review agent read-only.

## Permissions

Recommended default:

- read repository files
- read git diff
- read test output
- do not edit files during first review pass
- do not run network-dependent commands
- do not weaken tests
- do not merge

For CI:

- sandbox: `read-only`
- ask-for-approval: `never`

For local manual review:

- sandbox: `read-only` for first pass
- switch to `workspace-write` only after human approves a patching task

## Inputs

The review agent should receive:

- implementation prompt
- developer final report
- current git diff
- test output
- generated artifacts, if relevant
- `AGENTS.md`
- `docs/codex/post-development-review-agent.md`
- relevant phase guidance
- paper/protocol docs

## Outputs

The review agent must emit:

- verdict
- blocking issues
- non-blocking issues
- test assessment
- paper-boundary assessment
- phase-boundary assessment
- final recommendation

## Verdicts

Use:

- `ACCEPT`
- `ACCEPT WITH NON-BLOCKING NOTES`
- `REQUEST CHANGES`
- `REJECT`

## Blocking conditions

The review agent must block if the diff:

- upgrades runtime diagnostics into theorem-level claims
- emits `vinfo_proxy_supported` without fresh matching bridge evidence
- treats `CandidatePool` as a core paper artifact
- treats `gamma_hat` legacy/non-headline alias as a submodularity ratio
- treats `block_ratio_lcb_star` as paper-grade degree-adaptive
- performs live inference during Phase B
- recomputes diagnostics during Phase B
- infers missing materialization order
- infers excluded candidates without explicit complete set
- weakens tests or guardrails
- adds nondeterministic canonical outputs

## Human-in-the-loop rule

The review agent may recommend fixes, but it should not silently patch the implementation in the same pass.

Use this loop:

1. implementation agent produces diff
2. review agent audits diff
3. human accepts or rejects review findings
4. implementation agent patches only approved findings
5. review agent re-runs
